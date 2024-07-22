from firebase_admin import firestore
from firebase_config import initialize_firestore as db  # Assuming you have this import set up
from utils.logger import get_logger
from flask import jsonify

logger = get_logger(__name__)


def increment_unique_users(ip_address):
    unique_users_ref = db().collection('metrics').document('unique_users')
    unique_users_ref.set({
        ip_address: firestore.firestore.SERVER_TIMESTAMP
    }, merge=True)
    logger.info(f"Added unique user with IP address {ip_address}")


def increment_reports_generated():
    reports_ref = db().collection('metrics').document('reports_generated')
    reports_ref.set({
        'count': firestore.firestore.Increment(1)
    }, merge=True)
    logger.info("Incremented reports_generated metric")


def get_metrics():
    unique_users_doc = db().collection('metrics').document('unique_users').get()
    unique_users_count = len(unique_users_doc.to_dict()) if unique_users_doc.exists else 0

    reports_doc = db().collection('metrics').document('reports_generated').get()
    reports_count = reports_doc.to_dict().get('count', 0) if reports_doc.exists else 0

    return {
        'unique_users': unique_users_count,
        'reports_generated': reports_count
    }


def reset_metrics():
    db_instance = db()

    # Reset unique users
    unique_users_ref = db_instance.collection('metrics').document('unique_users')
    unique_users_ref.set({})

    # Reset reports generated
    reports_ref = db_instance.collection('metrics').document('reports_generated')
    reports_ref.set({
        'count': 0
    })

    logger.info("Metrics reset successfully")
