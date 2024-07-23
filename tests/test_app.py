# tests/test_app.py
import os

import pytest
import json
from app import app
from utils.version_info import get_version_info
from unittest.mock import patch
from flask import session


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"AION License Count" in response.data


def test_get_version_info():
    version_info = get_version_info()
    assert isinstance(version_info, dict)
    assert all(key in version_info for key in ['version', 'branch', 'date', 'build', 'environment'])


def test_upload_no_file(client):
    response = client.post('/upload', data={})
    assert response.status_code == 200
    assert b"Error" in response.data
    assert b"No File Uploaded" in response.data
    assert b"No file part in the request" in response.data


def test_upload_empty_filename(client):
    response = client.post('/upload', data={'file': (b'', '')})
    assert response.status_code == 200
    assert b"No File Selected" in response.data


# def test_upload_invalid_extension_redirect(client):
#     data = {'file': (b'content', 'test.txt')}
#     response = client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
#     assert response.status_code == 200
#     assert b"AION License Count" in response.data  # Check if it redirects back to the main page


def test_upload_invalid_csv(client, tmp_path):
    # Create a temporary CSV file with invalid content
    csv_content = b"InvalidColumn1,InvalidColumn2\nValue1,Value2"
    test_file = tmp_path / "invalid.csv"
    test_file.write_bytes(csv_content)

    with open(test_file, 'rb') as f:
        data = {'file': (f, 'invalid.csv'), 'cost_per_user': '115', 'cost_per_exchange': '20'}
        response = client.post('/upload', data=data, content_type='multipart/form-data')

    assert response.status_code == 200
    assert b"Invalid CSV File" in response.data


def test_upload_invalid_extension(client):
    data = {'file': (b'content', 'test.txt')}
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    assert b"Error" in response.data  # Check for the error page title
    assert b"No file part in the request" in response.data  # Check for the specific error message


def test_upload_valid_file(client, tmp_path):
    csv_content = b"Office,Licenses,User principal name,Display name\nOffice1,License1,user@example.com,User 1"
    test_file = tmp_path / "test.csv"
    test_file.write_bytes(csv_content)

    with open(test_file, 'rb') as f:
        data = {'file': (f, 'test.csv'), 'cost_per_user': '115', 'cost_per_exchange': '20'}
        with patch('app.process_file') as mock_process:
            mock_process.return_value = ('/path/to/result.xlsx', 'friendly_name.xlsx')
            response = client.post('/upload', data=data, content_type='multipart/form-data')

    assert response.status_code == 302  # Expect a redirect on successful upload
    assert response.headers['Location'].startswith('/summary/')
    os.remove(test_file)


def test_download_nonexistent_file(client):
    response = client.get('/download/nonexistent.xlsx')
    assert response.status_code == 200
    assert b"The requested file does not exist" in response.data


def test_show_summary_nonexistent_file(client):
    response = client.get('/summary/nonexistent.xlsx')
    assert response.status_code == 200
    assert b"An error occurred while generating the summary" in response.data


def test_cleanup_undownloaded_no_file_id(client):
    with client.session_transaction() as sess:
        sess.clear()
    response = client.post('/cleanup_undownloaded')
    assert response.status_code == 204


def test_cleanup_undownloaded_with_file_id(client, tmp_path):
    file_id = 'test_file_id'
    test_file = tmp_path / f"{file_id}_test.xlsx"
    test_file.touch()
    app.config['OUTPUT_FOLDER'] = str(tmp_path)

    with client.session_transaction() as sess:
        sess['pending_file_id'] = file_id

    response = client.post('/cleanup_undownloaded')
    assert response.status_code == 204
    assert not test_file.exists()


def test_check_session(client):
    with client.session_transaction() as sess:
        sess['pending_file_id'] = 'test_id'
        sess['friendly_filename'] = 'test.xlsx'

    response = client.get('/check_session')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['pending_file_id'] == 'test_id'
    assert data['friendly_filename'] == 'test.xlsx'


# Uncomment and modify this test when the get_logs route is enabled
# def test_get_logs(client, tmp_path):
#     log_file = tmp_path / "app.log"
#     log_file.write_text('{"level": "info", "event": "test_event", "timestamp": "2023-01-01T00:00:00"}\n')
#     app.config['LOG_DIR'] = str(tmp_path)
#
#     response = client.get('/api/logs')
#     assert response.status_code == 200
#     data = json.loads(response.data)
#     assert len(data['logs']) == 1
#     assert data['logs'][0]['event'] == 'test_event'

def test_page_not_found(client):
    response = client.get('/nonexistent_route')
    assert response.status_code == 404
    assert b"404 - Page Not Found" in response.data
