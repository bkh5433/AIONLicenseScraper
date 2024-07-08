import pandas as pd
import os
import openpyxl
import time
from datetime import datetime
from utils.logger import get_logger
from create_app import app

logger = get_logger(__name__)


def read_and_prepare_data(file_path):
    """Read CSV file and prepare the DataFrame by stripping whitespaces from the 'Office' column."""
    try:
        df = pd.read_csv(file_path)
        df['Office'] = df['Office'].str.strip()
        logger.info(f"csv cleaned successfully from {file_path}")
        return df
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except pd.errors.EmptyDataError:
        logger.error(f"No data: {file_path} is empty")
        return None
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None


def initialize_license_counts(df, target_licenses):
    """Initialize the license counts dictionary based on unique 'Office' values and target licenses."""
    license_counts = {office.strip(): {key: 0 for key in target_licenses.keys()}
                      for office in df['Office'].unique() if pd.notna(office) and office.strip()}
    license_counts['Unaccounted'] = {key: 0 for key in target_licenses.keys()}
    logger.info("Initialized license counts")
    return license_counts


def process_licenses(df, target_licenses, license_counts):
    """Process each row in the DataFrame to count licenses and log specific organizations."""
    logger.info("Processing licenses")
    unaccounted_users = []
    aion_management = []
    aion_partners = []
    properties = []

    for index, row in df.iterrows():
        office = row.get('Office')
        licenses = row.get('Licenses')
        user_principal_name = row.get('User principal name')
        display_name = row.get('Display name')

        if pd.isna(licenses) or licenses.strip() == '':
            continue

        licenses_list = licenses.split('+')

        for license in licenses_list:
            license = license.strip()

            for key, variants in target_licenses.items():
                if any(variant in license for variant in variants):
                    license_counts[office if not (pd.isna(office) or office.strip() == '') else 'Unaccounted'][key] += 1
                    if office == 'AION Management':
                        aion_management.append([display_name, license, user_principal_name])
                    elif office == 'AION Partners':
                        aion_partners.append([display_name, license, user_principal_name])
                    elif pd.isna(office) or office.strip() == '':
                        unaccounted_users.append([display_name, license, user_principal_name])
                    else:
                        properties.append([display_name, license, user_principal_name, office])

    logger.info("Processed licenses")
    return license_counts, unaccounted_users, aion_management, aion_partners, properties


def create_license_counts_df(license_counts):
    """Convert the license counts dictionary to a DataFrame and calculate totals."""
    try:
        license_counts_df = pd.DataFrame.from_dict(license_counts, orient='index').fillna(0)
        totals = license_counts_df.sum(axis=0).rename('Total')
        license_counts_df = pd.concat([license_counts_df, pd.DataFrame(totals).T])
        logger.info("Created license counts DataFrame")
        return license_counts_df
    except Exception as e:
        logger.error(f"Error creating license counts DataFrame: {e}")
        return None


def save_to_excel(excel_path, license_counts_df, aion_management_df, aion_partners_df, properties_df, unaccounted_users,
                  cost_per_user, cost_per_exchange):
    """Save the processed data to an Excel file with specific formatting."""
    try:
        logger.info(f"writing data to Excel file: {excel_path}")
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            license_counts_df.to_excel(writer, sheet_name='License Counts')
            aion_management_df.to_excel(writer, sheet_name='AION Management', index=False)
            aion_partners_df.to_excel(writer, sheet_name='AION Partners', index=False)
            properties_df.to_excel(writer, sheet_name='Properties', index=False)
            unaccounted_users.to_excel(writer, sheet_name='Unaccounted Users', index=False)

            workbook = writer.book
            header_format = workbook.add_format(
                {'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#D7E4BC', 'border': 1})
            total_format = workbook.add_format({'bold': True, 'fg_color': '#FFEB9C', 'border': 1,
                                                'num_format': '#,##0'})
            currency_format = workbook.add_format({'num_format': '$#,##0'})

            def format_sheet(worksheet, df, is_totals=False):
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num + 1 if is_totals else col_num, value, header_format)
                if is_totals:
                    worksheet.write(0, 0, 'Office', header_format)

                for col_num, col in enumerate(df.columns):
                    column_len = df[col].astype(str).str.len().max()
                    column_len = max(column_len, len(col)) + 2
                    worksheet.set_column(col_num + (1 if is_totals else 0), col_num + (1 if is_totals else 0),
                                         column_len)
                if is_totals:
                    worksheet.set_column(0, 0, max(df.index.astype(str).str.len().max(), len('Office')) + 2)

                worksheet.autofilter(0, 0, len(df), len(df.columns) + (1 if is_totals else 0) - 1)

            license_counts_worksheet = writer.sheets['License Counts']
            format_sheet(license_counts_worksheet, license_counts_df, is_totals=True)

            for col_num in range(len(license_counts_df.columns)):
                license_counts_worksheet.write(len(license_counts_df), col_num + 1, license_counts_df.iloc[-1, col_num],
                                               total_format)
            license_counts_worksheet.write(len(license_counts_df), 0, 'Total', total_format)

            # Set currency format for cost columns
            user_cost_col = 'Cost of Users (${})'.format(cost_per_user)
            exchange_cost_col = 'Cost of Exchange Licenses (${})'.format(cost_per_exchange)
            billable_total_col = 'Billable Total'

            user_cost_idx = license_counts_df.columns.get_loc(user_cost_col) + 1
            exchange_cost_idx = license_counts_df.columns.get_loc(exchange_cost_col) + 1
            billable_total_idx = license_counts_df.columns.get_loc(billable_total_col) + 1

            license_counts_worksheet.set_column(user_cost_idx, user_cost_idx, 15, currency_format)
            license_counts_worksheet.set_column(exchange_cost_idx, exchange_cost_idx, 15, currency_format)
            license_counts_worksheet.set_column(billable_total_idx, billable_total_idx, 15, currency_format)

            aion_management_worksheet = writer.sheets['AION Management']
            format_sheet(aion_management_worksheet, aion_management_df)

            aion_partners_worksheet = writer.sheets['AION Partners']
            format_sheet(aion_partners_worksheet, aion_partners_df)

            properties_worksheet = writer.sheets['Properties']
            format_sheet(properties_worksheet, properties_df)

            unaccounted_users_worksheet = writer.sheets['Unaccounted Users']
            format_sheet(unaccounted_users_worksheet, unaccounted_users)
        logger.info(f"Data saved to Excel file: {excel_path}")
    except PermissionError:
        logger.error(f"Permission denied when writing to {excel_path}")
    except Exception as e:
        logger.error(f"Error writing to Excel file {excel_path}: {e}")


def process_file(file_path, cost_per_user=115, cost_per_exchange=20):
    logger.info(f"Processing file: {file_path}")
    start_time = time.time()
    df = read_and_prepare_data(file_path)
    if df is None:
        return None

    target_licenses = {
        '365 Premium': ['Microsoft 365 Business Premium', 'E3'],
        'Exchange': ['Exchange']
    }

    license_counts = initialize_license_counts(df, target_licenses)
    license_counts, unaccounted_users, aion_management, aion_partners, properties = process_licenses(df,
                                                                                                     target_licenses,
                                                                                                     license_counts)

    license_counts_df = create_license_counts_df(license_counts)
    if license_counts_df is None:
        return None

    license_counts_df['Cost of Users (${})'.format(cost_per_user)] = license_counts_df['365 Premium'] * cost_per_user
    license_counts_df['Cost of Exchange Licenses (${})'.format(cost_per_exchange)] = license_counts_df[
                                                                                         'Exchange'] * cost_per_exchange
    license_counts_df['Billable Total'] = license_counts_df['Cost of Users (${})'.format(cost_per_user)] + \
                                          license_counts_df['Cost of Exchange Licenses (${})'.format(cost_per_exchange)]

    aion_management_df = pd.DataFrame(aion_management, columns=['Display Name', 'License Type', 'User Principal Name'])
    aion_partners_df = pd.DataFrame(aion_partners, columns=['Display Name', 'License Type', 'User Principal Name'])
    properties_df = pd.DataFrame(properties,
                                 columns=['Display Name', 'License Type', 'User Principal Name', 'Office'])
    unaccounted_users = pd.DataFrame(unaccounted_users, columns=['Display Name', 'License Type', 'User Principal Name'])

    current_date = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    excel_path = os.path.join(app.config['OUTPUT_FOLDER'], f"license_counts_{current_date}.xlsx")

    save_to_excel(excel_path, license_counts_df, aion_management_df, aion_partners_df, properties_df, unaccounted_users,
                  cost_per_user,
                  cost_per_exchange)
    logger.info(f"Processed file saved to: {excel_path}")

    try:
        os.remove(file_path)
        logger.info(f"Removed uploaded file: {file_path}")
    except OSError as e:
        logger.error(f"Error removing uploaded {file_path}: {e}")

    end_time = time.time()
    processing_time = end_time - start_time
    logger.info(f"CSV processing time: {processing_time:.2f} seconds")

    return excel_path


def generate_summary(file_path):
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook['License Counts']

    total_row = sheet.max_row
    data = [
        [sheet.cell(row=i, column=j).value for j in range(1, sheet.max_column + 1)]
        for i in range(2, total_row)  # Skip header row
    ]

    summary = {
        # Total number of 365 Premium licenses
        'total_365_premium': sum(row[1] for row in data),

        # Total number of Exchange licenses
        'total_exchange': sum(row[2] for row in data),

        # Total cost across all offices
        'total_cost': sum(row[5] for row in data),

        # Average cost per office
        'avg_cost_per_office': sum(row[5] for row in data) / len(data),

        # Highest cost among all offices
        'highest_cost': max(row[5] for row in data),

        # Name of the office with the highest cost
        'highest_cost_office': next(row[0] for row in data if row[5] == max(r[5] for r in data)),

        # Percentage of offices with both 365 Premium and Exchange licenses
        'percent_both_licenses': sum(1 for row in data if row[1] > 0 and row[2] > 0) / len(data) * 100,

        # Percentage of offices with only 365 Premium licenses
        'percent_only_365': sum(1 for row in data if row[1] > 0 and row[2] == 0) / len(data) * 100,

        # Percentage of offices with only Exchange licenses
        'percent_only_exchange': sum(1 for row in data if row[1] == 0 and row[2] > 0) / len(data) * 100,

        # Highest ratio of Exchange to 365 Premium licenses
        'highest_exchange_ratio': max((row[2] / row[1] if row[1] > 0 else 0) for row in data),

        # Name of the office with the highest Exchange to 365 Premium ratio
        'highest_exchange_ratio_office': next(row[0] for row in data if (row[2] / row[1] if row[1] > 0 else 0) == max(
            (r[2] / r[1] if r[1] > 0 else 0) for r in data)),

        # Number of offices with no licenses
        'offices_no_licenses': sum(1 for row in data if row[1] == 0 and row[2] == 0),

        # Average number of licenses (both types) per office
        'avg_licenses_per_office': (sum(row[1] for row in data) + sum(row[2] for row in data)) / len(data),

        # Top 5 offices by cost, sorted in descending order
        'top_offices_by_cost': sorted([(row[0], row[5]) for row in data], key=lambda x: x[1], reverse=True)[:5],

        # Top 5 offices by total number of licenses, sorted in descending order
        'top_offices_by_license': sorted([(row[0], row[1] + row[2]) for row in data], key=lambda x: x[1], reverse=True)[
                                  :5],
    }

    return summary
