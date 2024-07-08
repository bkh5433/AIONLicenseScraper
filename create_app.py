from flask import Flask
import os

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['INVALID_FOLDER'] = 'invalid'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}
app.config['LOG_DIR'] = 'logs'

# Create necessary directories
for folder in ['UPLOAD_FOLDER', 'OUTPUT_FOLDER', 'INVALID_FOLDER', 'LOG_DIR']:
    if not os.path.exists(app.config[folder]):
        os.makedirs(app.config[folder])
