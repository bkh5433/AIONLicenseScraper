from flask import jsonify
from utils.logger import get_logger
from firebase_config import initialize_firestore as db

logger = get_logger(__name__)


def reset_metrics():
    try:
        # Reset metrics in Firestore
        db_instance = db()
        metrics_ref = db_instance.collection('metrics').document('counts')
        metrics_ref.set({
            'unique_users': 0,
            'reports_generated': 0
        })
        logger.info("Metrics reset successfully")
        return jsonify({"message": "Metrics reset successfully"}), 200
    except Exception as e:
        logger.error(f"Error resetting metrics: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to reset metrics"}), 500
