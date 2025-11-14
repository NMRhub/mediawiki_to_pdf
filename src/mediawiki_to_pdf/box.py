from pathlib import Path
from typing import Iterable

import requests
from boxsdk import OAuth2, Client

from mediawiki_to_pdf import mediawiki_to_pdf_logger


def upload(config, files: Iterable[Path]):
    """Upload files to box using information from config"""
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
    new_names = set(f.name for f in files)
    for item in folder.get_items():
        if item.name in new_names:
            mediawiki_to_pdf_logger.info(f"Deleting existing {item.name}")
            item.delete()
    for file in files:
        uploaded_file = folder.upload(file.as_posix(), file.name)
        mediawiki_to_pdf_logger.info(f"Uploaded {uploaded_file}")
