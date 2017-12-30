import functools
import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud import firestore as g_firestore

PROJECT_ID = 'korni-stats'
CREDENTIALS_FILE_PATH = os.environ.get('KSC_FIREBASE_CRED', f'{Path.home()}/dev/korni-stats.json')


@functools.lru_cache(maxsize=1, typed=True)
def get_db() -> g_firestore.Client:
    if not os.path.exists(CREDENTIALS_FILE_PATH):
        raise RuntimeError(f'{CREDENTIALS_FILE_PATH} firebase credentials file does not exist')

    cred = credentials.Certificate(CREDENTIALS_FILE_PATH)

    firebase_admin.initialize_app(cred, {
        'projectId': PROJECT_ID,
    })

    return firestore.client()
