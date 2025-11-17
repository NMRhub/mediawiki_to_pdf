from pathlib import Path
from typing import Iterable

import requests
from boxsdk import OAuth2, Client

from mediawiki_to_pdf import mediawiki_to_pdf_logger

DEFAULT_MAP = {'pdf': False, 'txt': True}


def _find_matches(output: set, ext: str, source: Iterable[Path]) -> None:
    for file in source:
        if file.name.endswith(ext):
            output.add(file)


def upload(config, files: Iterable[Path], disposition_map: dict = None):
    """Upload files to box using information from config
    disposition_map > True to upload new version, False to replace file"""
    tmap = disposition_map if disposition_map is not None else DEFAULT_MAP
    id = config['client_id']
    secret = config['secret']
    folder_id = str(config['folder'])
    enterprise_id = config['enterprise id']  # You must add this to your config

    response = requests.post('https://api.box.com/oauth2/token', data={
        'grant_type': 'client_credentials',
        'client_id': id,
        'client_secret': secret,
        'box_subject_type': 'enterprise',
        'box_subject_id': enterprise_id
    })
    if response.status_code != 200:
        msg = getattr(response, 'text', "no message")
        raise ValueError(msg)

    response.raise_for_status()
    access_token = response.json()['access_token']

    oauth = OAuth2(client_id=id, client_secret=secret, access_token=access_token)
    client = Client(oauth)
    user = client.user().get()
    mediawiki_to_pdf_logger.info(f"Acting as: {user.id}  {user.name}")

    folder = client.folder(folder_id=folder_id)
    replacement_files = set()
    versioned_files = set()
    for extension, versioned in tmap.items():
        if versioned:
            _find_matches(versioned_files, extension, files)
        else:
            _find_matches(replacement_files, extension, files)
    unmapped = set(files) - replacement_files - versioned_files
    if unmapped:
        bad_names = ','.join(u.name for u in unmapped)
        raise ValueError(f"Unmapped extensions on {bad_names}")

    new_names = set(f.name for f in replacement_files)
    FETCH_LIMIT = 1000
    # noinspection PyUnresolvedReferences
    existing = {item.name: item for item in folder.get_items(limit=FETCH_LIMIT)}
    if len(existing) >= FETCH_LIMIT:
        raise ValueError(f"Only {FETCH_LIMIT} items in folder supported")

    for name in existing.keys():
        if name in new_names:
            mediawiki_to_pdf_logger.info(f"Deleting existing {name}")
            existing[name].delete()
    for file in replacement_files:
        uploaded_file = folder.upload(file.as_posix(), file.name)
        mediawiki_to_pdf_logger.info(f"Uploaded {uploaded_file}")

    for file in versioned_files:
        fname = file.name
        if fname in existing:
            # File exists → upload a new version
            mediawiki_to_pdf_logger.info(f"Updating version of {fname}")
            box_file = existing[fname]
            # noinspection PyUnresolvedReferences
            uploaded = box_file.update_contents(file.as_posix())
        else:
            # File does not exist → normal create
            mediawiki_to_pdf_logger.info(f"Uploading new file {fname}")
            uploaded = folder.upload(file.as_posix(), fname)

        mediawiki_to_pdf_logger.info(f"Uploaded: {uploaded}")
