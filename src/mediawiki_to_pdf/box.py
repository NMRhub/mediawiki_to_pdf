from pathlib import Path
from typing import Iterable, Dict, Set
import hashlib
import requests
from boxsdk import OAuth2, Client

from mediawiki_to_pdf import mediawiki_to_pdf_logger

DEFAULT_MAP = {'pdf': False, 'txt': True}


def sha1_file(path: Path) -> str:
    """Compute SHA-1 for a local file."""
    h = hashlib.sha1()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def _find_matches(output: Set[Path], ext: str, source: Iterable[Path]) -> None:
    """Collect files ending with a given extension."""
    for file in source:
        if file.name.endswith(ext):
            output.add(file)


def upload(config, files: Iterable[Path]):
    """
    Upload files to Box according to disposition_map.
    - True  → versioned upload (update if exists)
    - False → replacement upload (delete existing first)

    Only compute SHA-1 for versioned files.
    """
    client_id = config['client_id']
    secret = config['secret']
    folder_id = str(config['folder'])
    enterprise_id = config['enterprise id']
    tmap = config['disposition map']

    # --- Get enterprise token -------------------------------------------------
    response = requests.post(
        'https://api.box.com/oauth2/token',
        data={
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': secret,
            'box_subject_type': 'enterprise',
            'box_subject_id': enterprise_id,
        },
    )
    if response.status_code != 200:
        msg = getattr(response, 'text', "no error text")
        raise ValueError(msg)

    response.raise_for_status()
    access_token = response.json()['access_token']

    oauth = OAuth2(client_id=client_id, client_secret=secret, access_token=access_token)
    client = Client(oauth)

    user = client.user().get()
    mediawiki_to_pdf_logger.info(f"Acting as: {user.id}  {user.name}")

    # --- Organize input files by disposition ----------------------------------
    folder = client.folder(folder_id=folder_id)
    replacement_files: Set[Path] = set()
    versioned_files: Set[Path] = set()

    for extension, versioned in tmap.items():
        if versioned:
            _find_matches(versioned_files, extension, files)
        else:
            _find_matches(replacement_files, extension, files)

    unmapped = set(files) - replacement_files - versioned_files
    if unmapped:
        bad_names = ','.join(u.name for u in unmapped)
        raise ValueError(f"Unmapped extensions on {bad_names}")

    new_replacement_names = {f.name for f in replacement_files}

    # --- Retrieve existing items ---------------------------------------------
    FETCH_LIMIT = 1000
    # noinspection PyUnresolvedReferences
    existing: Dict[str, object] = {
        item.name: item for item in folder.get_items(limit=FETCH_LIMIT)
    }

    if len(existing) >= FETCH_LIMIT:
        raise ValueError(f"Folder has >= {FETCH_LIMIT} items; increase FETCH_LIMIT")

    # --- Replacement files: delete then upload fresh --------------------------
    for name in new_replacement_names:
        if name in existing:
            mediawiki_to_pdf_logger.info(f"Deleting existing {name}")
            existing[name].delete()

    for file in replacement_files:
        uploaded_file = folder.upload(file.as_posix(), file.name)
        mediawiki_to_pdf_logger.info(f"Uploaded replacement: {uploaded_file}")

    # --- Versioned files: update only if content changed ----------------------
    for file in versioned_files:
        fname = file.name

        if fname in existing:
            box_file = existing[fname]

            # Fetch remote SHA-1
            # noinspection PyUnresolvedReferences
            remote = box_file.get(fields=['sha1'])
            remote_sha1 = (remote.sha1 or "").lower()

            # Compute local SHA-1 ONLY for versioned files
            local_sha1 = sha1_file(file)

            if remote_sha1 == local_sha1.lower():
                mediawiki_to_pdf_logger.info(
                    f"Skipping unchanged file {fname} (SHA-1 identical)"
                )
                continue

            # Only update when content differs
            mediawiki_to_pdf_logger.info(f"Updating version of {fname}")
            # noinspection PyUnresolvedReferences
            uploaded = box_file.update_contents(file.as_posix())

        else:
            # No remote file — upload new
            mediawiki_to_pdf_logger.info(f"Uploading new file {fname}")
            uploaded = folder.upload(file.as_posix(), fname)

        mediawiki_to_pdf_logger.info(f"Uploaded versioned: {uploaded}")

