from flask import render_template, request, redirect, url_for, send_from_directory, jsonify
from csv_parser import process_file
from create_app import app
from validation import validate_csv
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                    filename='/app/logs/app.log', encoding='utf-8')
logger = logging.getLogger(__name__)


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
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            logger.warning("No file part in the request")
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            logger.warning("No selected file")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            logger.info(f"File uploaded: {file.filename}")

            is_valid, error_message = validate_csv(file_path)
            if not is_valid:
                invalid_path = os.path.join(app.config['INVALID_FOLDER'], file.filename)
                os.rename(file_path, invalid_path)
                logger.error(f"File validation failed: {file.filename} - {error_message}")
                return render_template('error.html', error_message=error_message)

            result_path = process_file(file_path)
            logger.info(f"File processed successfully: {file.filename}")
            return redirect(url_for('download_file', filename=os.path.basename(result_path)))

        logger.warning(f"File extension not allowed: {file.filename}")
        return redirect(request.url)
    except Exception as e:
        logger.exception("An error occurred during file upload")
        return render_template('error.html', error_message="An unexpected error occurred. Please try again.")


@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        response = send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)
        logger.info(f"File downloaded: {filename}")
        os.remove(file_path)  # Remove the file after download
        return response
    except Exception as e:
        logger.exception("An error occurred during file download")
        return render_template('error.html', error_message="An error occurred while trying to download the file.")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
