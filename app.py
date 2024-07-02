from flask import render_template, request, redirect, url_for, send_from_directory
from csv_parser import process_file
from create_app import app
from utils.validation import validate_csv
from utils.logger import setup_logging, get_logger
import os
import json

setup_logging()
logger = get_logger(__name__)


def get_version_info():
    try:
        with open('version.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"version": "unknown", "commit": "unknown", "date": "unknown"}


@app.context_processor
def inject_version():
    return dict(version_info=get_version_info())


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.before_request
def log_request_start():
    logger.info(f"Start processing request: {request.method} {request.path}")


@app.after_request
def log_request_end(response):
    logger.info(f"Finished processing request: {request.method} {request.path} with status {response.status_code}")
    return response


@app.route('/')
def index():
    logger.info("Rendering upload page")
    logger.info(f"App version: {get_version_info()}")
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
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

            result_path = process_file(file_path, int(cost_per_user), int(cost_per_exchange))
            logger.info(f"File processed successfully: {file.filename}")
            return redirect(url_for('download_file', filename=os.path.basename(result_path)))

        logger.warning(f"File extension not allowed: {file.filename}")
        return redirect(request.url)
    except Exception as e:
        logger.exception("An error occurred during file upload")
        return render_template('error.html',
                               error_title=f"An unexpected error occurred. Please try again.",
                               error_message=str(e))


@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        response = send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)
        if response.status_code == 200:
            logger.info(f"File downloaded: {filename}")
        else:
            logger.error(f"Error downloading file: {filename}")
            logger.error(response)
        try:
            os.remove(file_path)  # Remove the file after download
            logger.info(f"Removed downloaded file: {filename}")
        except OSError as e:
            logger.error(f"Error removing file {filename}: {e}")
        return response
    except Exception as e:
        logger.exception(f"An error occurred during file download\n {e}")
        return render_template('error.html',
                               error_message=f"An error occurred while trying to download the file.\n {e}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
