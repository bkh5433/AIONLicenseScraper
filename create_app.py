"""
Application configuration module for the AION License Count application.

This module initializes the Flask application, sets up configuration variables,
and creates necessary directories for file handling and logging.
"""
from flask import Flask
import os
import json

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads'  # Directory for uploaded files
app.config['OUTPUT_FOLDER'] = 'output'  # Directory for output files
app.config['INVALID_FOLDER'] = 'invalid'  # Directory for invalid files
app.config['ALLOWED_EXTENSIONS'] = {'csv'}  # Allowed file extensions
app.config['LOG_DIR'] = 'logs'  # Directory for log files

# Create necessary directories
for folder in ['UPLOAD_FOLDER', 'OUTPUT_FOLDER', 'INVALID_FOLDER', 'LOG_DIR']:
    if not os.path.exists(app.config[folder]):
        os.makedirs(app.config[folder])

try:
    with open('version.json', 'r') as f:
        version_info = json.load(f)
    app.secret_key = version_info.get('secret_key') or os.urandom(24).hex()
except (FileNotFoundError, json.JSONDecodeError):
    app.secret_key = os.urandom(24).hex()

# Note: The 'app' object is imported by other modules to access
# the Flask application instance and its configurations.
