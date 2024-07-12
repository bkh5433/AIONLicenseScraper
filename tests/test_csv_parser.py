# tests/test_csv_parser.py

import pytest
import pandas as pd
import os
from csv_parser import (
    read_and_prepare_data,
    initialize_license_counts,
    process_licenses,
    create_license_counts_df,
    process_file,
    generate_summary
)
from unittest.mock import patch, MagicMock
from .test_data_generator import generate_test_csv


@pytest.fixture
def sample_csv(tmp_path):
    return generate_test_csv(tmp_path, num_rows=100)


@pytest.fixture
def large_sample_csv(tmp_path):
    return generate_test_csv(tmp_path, num_rows=10000)


def test_read_and_prepare_data(sample_csv):
    df = read_and_prepare_data(sample_csv)
    assert isinstance(df, pd.DataFrame)
    assert 'Office' in df.columns
    assert df['Office'].str.strip().equals(df['Office'])
    assert len(df) == 100


def test_read_and_prepare_data_file_not_found():
    df = read_and_prepare_data("non_existent_file.csv")
    assert df is None


def test_initialize_license_counts(sample_csv):
    df = read_and_prepare_data(sample_csv)
    target_licenses = {
        '365 Premium': ['Microsoft 365 Business Premium', 'Microsoft 365 E3', 'Microsoft 365 E5'],
        'Exchange': ['Exchange Online (Plan 1)', 'Exchange Online (Plan 2)']
    }
    license_counts = initialize_license_counts(df, target_licenses)
    assert 'AION Management' in license_counts
    assert 'AION Partners' in license_counts
    assert 'Unaccounted' in license_counts
    assert all(key in license_counts['AION Management'] for key in target_licenses.keys())


def test_process_licenses(sample_csv):
    df = read_and_prepare_data(sample_csv)
    target_licenses = {
        '365 Premium': ['Microsoft 365 Business Premium', 'Microsoft 365 E3', 'Microsoft 365 E5'],
        'Exchange': ['Exchange Online (Plan 1)', 'Exchange Online (Plan 2)']
    }
    license_counts = initialize_license_counts(df, target_licenses)
    result = process_licenses(df, target_licenses, license_counts)

    assert len(result) == 5  # license_counts, unaccounted_users, aion_management, aion_partners, properties
    assert sum(sum(office.values()) for office in result[0].values()) > 0  # Ensure some licenses were counted


def test_create_license_counts_df():
    license_counts = {
        'Office1': {'365 Premium': 1, 'Exchange': 0},
        'Office2': {'365 Premium': 0, 'Exchange': 1},
        'Unaccounted': {'365 Premium': 0, 'Exchange': 1}
    }
    df = create_license_counts_df(license_counts)
    assert isinstance(df, pd.DataFrame)
    assert 'Total' in df.index
    assert df.loc['Total', '365 Premium'] == 1
    assert df.loc['Total', 'Exchange'] == 2


def test_process_large_file(large_sample_csv):
    df = read_and_prepare_data(large_sample_csv)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 10000

    target_licenses = {
        '365 Premium': ['Microsoft 365 Business Premium', 'Microsoft 365 E3', 'Microsoft 365 E5'],
        'Exchange': ['Exchange Online (Plan 1)', 'Exchange Online (Plan 2)']
    }
    license_counts = initialize_license_counts(df, target_licenses)
    result = process_licenses(df, target_licenses, license_counts)

    assert len(result) == 5  # license_counts, unaccounted_users, aion_management, aion_partners, properties
    assert sum(sum(office.values()) for office in result[0].values()) > 0  # Ensure some licenses were counted


@patch('csv_parser.read_and_prepare_data')
@patch('csv_parser.save_to_excel')
@patch('os.remove')
def test_process_file(mock_remove, mock_save_to_excel, mock_read_and_prepare_data, sample_csv, tmp_path):
    df = read_and_prepare_data(sample_csv)
    mock_read_and_prepare_data.return_value = df

    result = process_file(str(sample_csv))

    assert isinstance(result, tuple)
    assert len(result) == 2
    assert result[0].endswith('.xlsx')
    assert result[1].startswith('AION_License_Report_')
    mock_save_to_excel.assert_called_once()
    mock_remove.assert_called_once_with(str(sample_csv))


# @patch('openpyxl.load_workbook')
# def test_generate_summary(mock_load_workbook):
#     # Create more realistic mock data with a header row
#     mock_data = [
#         ['Office', '365 Premium', 'Exchange', 'Cost of Users ($115)', 'Cost of Exchange Licenses ($20)', 'Billable Total'],
#         ['Office1', 10, 5, 1150, 100, 1250],
#         ['Office2', 5, 10, 575, 200, 775],
#         ['Office3', 15, 0, 1725, 0, 1725],
#     ]
#
#     mock_sheet = MagicMock()
#     mock_sheet.max_row = len(mock_data)
#     mock_sheet.iter_rows.return_value = [[MagicMock(value=v) for v in row] for row in mock_data]
#
#     mock_workbook = MagicMock()
#     mock_workbook.__getitem__.return_value = mock_sheet
#     mock_load_workbook.return_value = mock_workbook
#
#     summary = generate_summary('dummy_path')
#
#     assert isinstance(summary, dict)
#     assert summary['total_365_premium'] == 30
#     assert summary['total_exchange'] == 15
#     assert summary['total_cost'] == 3750
#     assert summary['avg_cost_per_office'] == 1250
#     assert summary['highest_cost'] == 1725
#     assert summary['highest_cost_office'] == 'Office3'
#     assert summary['percent_both_licenses'] == pytest.approx(66.67, 0.01)
#     assert summary['percent_only_365'] == pytest.approx(33.33, 0.01)
#     assert summary['percent_only_exchange'] == 0
#     assert summary['highest_exchange_ratio'] == 2
#     assert summary['highest_exchange_ratio_office'] == 'Office2'
#     assert summary['offices_no_licenses'] == 0
#     assert summary['avg_licenses_per_office'] == 15
#     assert len(summary['top_offices_by_cost']) == 3
#     assert len(summary['top_offices_by_license']) == 3


def test_end_to_end_processing(sample_csv, tmp_path):
    # This test simulates the entire process from CSV to summary generation
    result_path, friendly_filename = process_file(str(sample_csv))

    assert os.path.exists(result_path)
    assert friendly_filename.startswith('AION_License_Report_')

    summary = generate_summary(result_path)

    assert isinstance(summary, dict)
    assert summary['total_365_premium'] > 0 or summary['total_exchange'] > 0
    assert summary['total_cost'] > 0
    assert len(summary['top_offices_by_cost']) > 0
    assert len(summary['top_offices_by_license']) > 0

    # Clean up the generated file
    os.remove(result_path)
