from flask import render_template, request, redirect, url_for, send_from_directory, jsonify
import os
from csv_parser import process_file
from create_app import app
from validation import validate_csv


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        is_valid, error_message = validate_csv(file_path)
        if not is_valid:
            return jsonify({'error': error_message}), 400
        result_path = process_file(file_path)
        return redirect(url_for('download_file', filename=os.path.basename(result_path)))
    return redirect(request.url)


@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    response = send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)
    os.remove(file_path)  # Remove the file after download
    return response


if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=8000)
