"""
Main application module for the AION License Count application.

This module sets up the Flask application, defines routes, and handles
file uploads, processing, and downloads.
"""

from flask import render_template, request, redirect, url_for, session, Response, g, after_this_request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask.json import jsonify
from csv_parser import process_file, generate_summary
from create_app import app
from utils.validation import validate_csv
from utils.logger import setup_logging, get_logger
from utils.version_info import get_version_info
from datetime import datetime, timezone
from collections import Counter
from functools import wraps
from firebase_config import initialize_firestore
from werkzeug.security import check_password_hash
from models import User
from metrics import increment_unique_users, increment_reports_generated, reset_metrics
from metrics import get_metrics as get_metrics
from firebase_config import initialize_firestore as db
import os
import json
import time

setup_logging()
logger = get_logger(__name__)
unique_users = set()
reports_generated = Counter()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def custom_jsonify(*args, **kwargs):
    return app.response_class(
        json.dumps(dict(*args, **kwargs), cls=CustomJSONEncoder),
        mimetype='application/json'
    )


app.json_encoder = CustomJSONEncoder


@login_manager.user_loader
def load_user(user_id):
    user_doc = db().collection('users').document(user_id).get()
    if user_doc.exists:
        return User(user_id)
    return None


@app.context_processor
def inject_version():
    """
      Inject version information into all templates.

      Returns:
          dict: A dictionary containing version information.
      """
    return dict(version_info=get_version_info())


@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        logger.info("Initializing Firestore")
        initialize_firestore()

        logger.info("Admin user initialization completed")
    except Exception as e:
        logger.error(f"Error fetching admin user: {str(e)}", exc_info=True)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_ref = db().collection('users').document(username)
        user_doc = user_ref.get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            if check_password_hash(user_data['password_hash'], password):
                user = User(username)  # You'll need to define a simple User class
                login_user(user)
                return redirect(url_for('admin_center'))
        return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(e):
    """
     Handle 404 errors.

     Args:
         e: The error object.

     Returns:
         tuple: A tuple containing the rendered 404 template and the 404 status code.
     """
    logger.warning(f"Page not found {e}")
    return render_template('404.html'), 404


def allowed_file(filename):
    """
    Check if the file extension is allowed.

    Args:
        filename (str): The name of the file to check.

    Returns:
        bool: True if the file extension is allowed, False otherwise.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.before_request
def log_request_start():
    """
    Log the start of each request.
    """
    logger.info(f"Start processing request: {request.method} {request.path}")


@app.after_request
def log_request_end(response):
    """
    Log the end of each request.

    Args:
        response: The response object.

    Returns:
        response: The unmodified response object.
    """
    logger.info(f"Finished processing request: {request.method} {request.path} with status {response.status_code}")
    return response


@app.route('/')
def index():
    """
      Render the upload page.

      Returns:
          str: Rendered HTML for the upload page.
      """
    logger.info("Rendering upload page")
    logger.info(f"App version: {get_version_info()}")
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """
       Handle file uploads, validate the file, and process it.

       Returns:
           str: Redirects to the summary page on success, or renders an error page on failure.
       """
    global unique_users, reports_generated
    start_time = time.time()
    unique_users.add(request.headers.get('X-Forwarded-For', request.remote_addr))

    try:
        if 'file' not in request.files:
            logger.warning("No file part in the request")
            return render_template('error.html',
                                   error_title='No File Uploaded',
                                   error_message="No file part in the request")

        file = request.files['file']
        cost_per_user = request.form.get('cost_per_user', 115)
        cost_per_exchange = request.form.get('cost_per_exchange', 20)

        if file.filename == '':
            logger.warning("No selected file")
            return render_template('error.html',
                                   error_title='No File Selected',
                                   error_message="Please choose a file before uploading.")

        if file and allowed_file(file.filename):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            logger.info(f"File uploaded: {file.filename}")

            is_valid, error_message = validate_csv(file_path)
            if not is_valid:
                invalid_path = os.path.join(app.config['INVALID_FOLDER'], file.filename)
                os.rename(file_path, invalid_path)
                logger.error(f"File validation failed: {file.filename} - {error_message}")
                return render_template('error.html',
                                       error_title='Invalid CSV File',
                                       error_message=error_message)

            result_path, friendly_filename = process_file(file_path, int(cost_per_user), int(cost_per_exchange))

            increment_unique_users(request.headers.get('X-Forwarded-For', request.remote_addr))
            increment_reports_generated()

            logger.info(f"File processed successfully: {file.filename}")
            file_id = os.path.basename(result_path).split('_')[0]
            if file_id:
                session['pending_file_id'] = file_id
                session['friendly_filename'] = friendly_filename
                logger.info(f"Set pending file ID in session: {file_id}")
            else:
                logger.warning(f"Unable to extract file ID from filename: {os.path.basename(result_path)}")

            end_time = time.time()
            processing_time = end_time - start_time
            logger.info(f"Processing time for upload: {processing_time:.2f} seconds")

            time.sleep(1)  # Wait for the file to be written to disk
            return redirect(url_for('show_summary', filename=os.path.basename(result_path)))

        logger.warning(f"File extension not allowed: {file.filename}")
        return redirect(request.url)
    except Exception as e:
        logger.exception("An error occurred during file upload")
        return render_template('error.html',
                               error_title=f"An unexpected error occurred. Please try again.",
                               error_message=str(e))


@app.route('/download/<filename>')
def download_file(filename):
    """
    Handle file downloads and remove the file after successful download.

    Args:
        filename (str): The name of the file to download.

    Returns:
        flask.Response: The file download response or an error page.
    """
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if not os.path.exists(file_path):
            logger.error(f"File not found: {filename}")
            return render_template('error.html',
                                   error_message=f"The requested file does not exist.")

        friendly_filename = session.get('friendly_filename', filename)

        # Store necessary session data before the request context is torn down
        session.pop('pending_file_id', None)
        session.pop('friendly_filename', None)
        logger.info(f"Cleared session data for: {filename}")

        def generate():
            with open(file_path, 'rb') as f:
                yield from f

        def cleanup():
            try:
                os.remove(file_path)
                logger.info(f"Removed downloaded file: {filename}")
            except Exception as e:
                logger.error(f"Error in cleanup after download for {filename}: {e}")

        response = Response(generate(), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response.headers["Content-Disposition"] = f"attachment; filename={friendly_filename}"
        response.call_on_close(cleanup)
        return response

    except Exception as e:
        logger.exception(f"An unexpected error occurred during file download: {e}")
        return render_template('error.html',
                               error_message=f"An unexpected error occurred while trying to download the file: {e}")


@app.route('/summary/<filename>')
def show_summary(filename):
    """
    Generate and display the summary page for a processed file.

    Args:
        filename (str): The name of the processed file.

    Returns:
        str: Rendered HTML for the summary page or an error page.
    """

    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        summary_data = generate_summary(file_path)
        user_friendly_filename = session.get('friendly_filename', filename)
        return render_template('summary.html', summary=summary_data,
                               filename=filename,
                               user_friendly_filename=user_friendly_filename)
    except Exception as e:
        logger.exception("An error occurred while generating summary")
        return render_template('error.html',
                               error_title="An error occurred while generating the summary.",
                               error_message=str(e))


@app.route('/cleanup_undownloaded', methods=['POST'])
def cleanup_undownloaded():
    import datetime

    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    logger.info(f"Cleanup process initiated at {current_time}")
    file_id = session.get('pending_file_id')
    logger.info(f"File ID from session: {file_id}")
    if file_id:
        output_folder = app.config['OUTPUT_FOLDER']
        logger.info(f"Attempting to clean up undownloaded file with prefix: {file_id}")
        files_found = False
        for filename in os.listdir(output_folder):
            if filename.startswith(str(file_id)):
                files_found = True
                file_path = os.path.join(output_folder, filename)
                try:
                    os.remove(file_path)
                    logger.info(f"Cleaned up undownloaded file: {filename}")
                except OSError as e:
                    logger.error(f"Error removing undownloaded file {filename}: {e}")
        if not files_found:
            logger.warning(f"No files found with prefix {file_id}")
        session.pop('pending_file_id', None)
        session.pop('friendly_filename', None)
        logger.info("Cleared session data")
    else:
        logger.warning("No file ID found in session for cleanup")
    return '', 204


@app.route('/admin')
@login_required
def admin_center():
    return render_template('admin_center.html')


@app.route('/check_session')
def check_session():
    return custom_jsonify({
        'pending_file_id': session.get('pending_file_id'),
        'friendly_filename': session.get('friendly_filename')
    })


def api_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return custom_jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)

    return decorated_function


@app.route('/api/logs', methods=['GET'])
@api_login_required
def get_logs():
    log_file_path = os.path.join(app.config['LOG_DIR'], 'app.log')
    level = request.args.get('level', '').lower()
    search = request.args.get('search', '').lower()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    http_method = request.args.get('http_method', '').upper()
    exclude_api = request.args.get('exclude_api', 'false').lower() == 'true'
    ip_address = request.args.get('ip_address', '')
    path = request.args.get('path', '')
    user_agent = request.args.get('user_agent', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))

    def parse_timestamp(timestamp):
        if isinstance(timestamp, datetime):
            return timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp
        elif isinstance(timestamp, str):
            timestamp = timestamp.rstrip('Z')  # Remove trailing 'Z' if present
            try:
                return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
            except ValueError:
                try:
                    return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                except ValueError:
                    return datetime.min.replace(tzinfo=timezone.utc)
        else:
            return datetime.min.replace(tzinfo=timezone.utc)

    all_logs = []
    with open(log_file_path, 'r') as log_file:
        for line in log_file:
            try:
                log_entry = json.loads(line.strip())
            except json.JSONDecodeError:
                log_entry = {
                    "level": "ERROR",
                    "event": line.strip(),
                    "timestamp": datetime.now().isoformat()
                }

            log_entry['parsed_timestamp'] = parse_timestamp(log_entry.get('timestamp', ''))
            all_logs.append(log_entry)

    # Sort all logs by timestamp in descending order
    all_logs.sort(key=lambda x: parse_timestamp(x.get('timestamp', '')), reverse=True)

    # Apply filters
    filtered_logs = []
    for log in all_logs:
        if (not level or log.get('level', '').lower() == level) and \
                (not start_date or parse_timestamp(log.get('timestamp', '')) >= parse_timestamp(start_date)) and \
                (not end_date or parse_timestamp(log.get('timestamp', '')) <= parse_timestamp(end_date)) and \
                (not http_method or log.get('method', '').upper() == http_method) and \
                (not ip_address or log.get('ip', '') == ip_address) and \
                (not path or path in log.get('path', '')) and \
                (not user_agent or user_agent in log.get('user_agent', '')) and \
                (not exclude_api or not log.get('path', '').startswith('/api/')):

            log_copy = log.copy()
            for key, value in log_copy.items():
                if isinstance(value, datetime):
                    log_copy[key] = value.isoformat()

            if not search or search.lower() in json.dumps(log_copy, cls=CustomJSONEncoder).lower():
                filtered_logs.append(log_copy)

    # Calculate pagination
    total_logs = len(filtered_logs)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_logs = filtered_logs[start:end]

    # Prepare logs for output
    for log in paginated_logs:
        log['timestamp'] = parse_timestamp(log.get('timestamp', '')).isoformat()
        if 'parsed_timestamp' in log:
            del log['parsed_timestamp']
        if 'event' not in log and 'message' in log:
            log['event'] = log['message']
        if 'event' not in log:
            log['event'] = 'No event provided'
        if 'level' not in log:
            log['level'] = 'INFO'
        for key, value in log.items():
            if not isinstance(value, (str, int, float, bool, type(None))):
                log[key] = str(value)

    return custom_jsonify({
        'logs': paginated_logs,
        'total': total_logs,
        'page': page,
        'per_page': per_page,
        'total_pages': (total_logs + per_page - 1) // per_page
    })


@app.route('/api/metrics')
@api_login_required
def api_get_metrics():
    try:
        metrics = get_metrics()
        return jsonify(metrics)
    except Exception as e:
        logger.exception("Error occurred while fetching metrics", exc_info=e)
        return jsonify({'error': 'An error occurred while fetching metrics'}), 500


@app.route('/api/reset_metrics', methods=['POST'])
@api_login_required
def api_reset_metrics():
    try:
        reset_metrics()
        return jsonify({"message": "Metrics reset successfully"}), 200
    except Exception as e:
        logger.exception("Error occurred while resetting metrics", exc_info=True)
        return jsonify({"error": "Failed to reset metrics"}), 500


@app.errorhandler(Exception)
def handle_exception(e):
    # Log the exception
    logger.exception("Unhandled exception occurred")
    # Return an error page with the exception message
    return render_template('error.html', error_message=str(e)), 500


# @app.route('/test-exception')
# def test_exception():
#     logger = get_logger(__name__)
#     try:
#         raise ValueError("This is a test exception")
#     except Exception as e:
#         logger.exception("An error occurred in the test route")
#         raise

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200


if __name__ == '__main__':
    try:
        logger.info("Initializing Firestore")
        initialize_firestore()

        logger.info("Starting Flask app")
        app.run(host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Error during application startup: {str(e)}", exc_info=True)
