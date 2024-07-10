import pytest
from utils.validation import validate_csv


def test_validate_csv_valid_file(tmp_path):
    d = tmp_path / "test_dir"
    d.mkdir()
    p = d / "valid.csv"
    p.write_text("Office,Licenses,User principal name,Display name\nOffice1,License1,user@example.com,User 1")

    is_valid, error_message = validate_csv(str(p))
    assert is_valid
    assert error_message is None


def test_validate_csv_missing_columns(tmp_path):
    d = tmp_path / "test_dir"
    d.mkdir()
    p = d / "invalid.csv"
    p.write_text("Office,Licenses\nOffice1,License1")

    is_valid, error_message = validate_csv(str(p))
    assert not is_valid
    assert "Missing columns" in error_message

# Add more tests for other validation scenarios
