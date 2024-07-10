"""
Main application module for the AION License Count application.

This module sets up the Flask application, defines routes, and handles
file uploads, processing, and downloads.
"""

from flask import render_template, request, redirect, url_for, send_from_directory, jsonify, session, Response
from csv_parser import process_file, generate_summary
from create_app import app
from utils.validation import validate_csv
from utils.logger import setup_logging, get_logger
import os
import json
import time
import datetime

setup_logging()
logger = get_logger(__name__)


def get_version_info():
    """
        Retrieve version information from environment variables or version.json file.

        Returns:
            dict: A dictionary containing version information with keys:
                  version, branch, date, build, and environment.
        """

    # First, try to get version info from environment variables
    version = os.environ.get('APP_VERSION')
    branch = os.environ.get('APP_BRANCH')
    date = os.environ.get('APP_BUILD_DATE')
    build = os.environ.get('APP_BUILD')
    environment = os.environ.get('APP_ENVIRONMENT')

    # If any of the environment variables are not set, try to read from version.json
    if not all([version, branch, date, build, environment]):
        try:
            with open('version.json', 'r') as f:
                version_data = json.load(f)
                version = version_data.get('version', 'unknown')
                branch = version_data.get('branch', 'unknown')
                date = version_data.get('date', 'unknown')
                build = version_data.get('build', 'unknown')
                environment = version_data.get('environment', 'unknown')
        except FileNotFoundError:
            # If version.json doesn't exist, use default values
            version = version or 'unknown'
            branch = branch or 'unknown'
            date = date or 'unknown'
            build = build or 'unknown'
            environment = environment or 'unknown'

    return {
        "version": version,
        "branch": branch,
        "date": date,
        "build": build,
        "environment": environment
    }


@app.context_processor
def inject_version():
    """
      Inject version information into all templates.

      Returns:
          dict: A dictionary containing version information.
      """
    return dict(version_info=get_version_info())


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
    start_time = time.time()

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

        def generate():
            with open(file_path, 'rb') as f:
                yield from f

            # Cleanup after file has been sent
            try:
                os.remove(file_path)
                logger.info(f"Removed downloaded file: {filename}")
                session.pop('pending_file_id', None)
                session.pop('friendly_filename', None)
                logger.info(f"Cleared session data for: {filename}")
            except Exception as e:
                logger.error(f"Error in cleanup after download for {filename}: {e}")

        response = Response(generate(), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response.headers["Content-Disposition"] = f"attachment; filename={friendly_filename}"
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


@app.route('/check_session')
def check_session():
    return jsonify({
        'pending_file_id': session.get('pending_file_id'),
        'friendly_filename': session.get('friendly_filename')
    })


# TODO: Uncomment the following route to enable the logs API
# @app.route('/api/logs', methods=['GET'])
def get_logs():
    log_file_path = os.path.join(app.config['LOG_DIR'], 'app.log')
    invalid_lines = 0
    try:
        logs = []
        invalid = []

        with open(log_file_path, 'r') as log_file:
            for line in log_file:
                try:
                    log_entry = json.loads(line.strip())
                    logs.append(log_entry)
                except json.JSONDecodeError:
                    invalid_lines += 1
                    invalid.append(line)
                    # Skip invalid JSON lines
                    continue

        # Filter logs based on query parameters
        level = request.args.get('level')
        if level:
            logs = [log for log in logs if log.get('level') == level.lower()]

        # Filter by event
        event = request.args.get('event')
        if event:
            logs = [log for log in logs if event.lower() in log.get('event', '').lower()]

        # Filter by time range
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        if start_time:
            logs = [log for log in logs if log.get('timestamp', '') >= start_time]
        if end_time:
            logs = [log for log in logs if log.get('timestamp', '') <= end_time]

        # Get the last n lines
        limit = request.args.get('limit', type=int)
        if limit:
            logs = logs[-limit:]

        return jsonify({'logs': logs}), 200
    except FileNotFoundError:
        return jsonify({'error': 'Log file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
