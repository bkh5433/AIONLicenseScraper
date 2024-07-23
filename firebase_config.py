import firebase_admin
from firebase_admin import credentials, firestore, auth
from utils.logger import get_logger

logger = get_logger(__name__)


def initialize_firestore():
    logger.info("Checking Firebase initialization status")
    try:
        firebase_admin.get_app()
        logger.info('Firebase app is already initialized')
    except ValueError:
        logger.info('Firebase app has not been initialized')

    if not firebase_admin._apps:
        logger.info("Initializing Firebase app")
        cred = credentials.Certificate('firebase/fb-key.json')
        firebase_admin.initialize_app(cred)
        logger.info('Firebase app initialized successfully')

    fs = firestore.client()
    logger.info('Firestore client created')
    return fs
