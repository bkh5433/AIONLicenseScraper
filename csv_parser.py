import pandas as pd
import os
import openpyxl
from datetime import datetime
from utils.logger import get_logger
from create_app import app

logger = get_logger(__name__)


def read_and_prepare_data(file_path):
    """Read CSV file and prepare the DataFrame by stripping whitespaces from the 'Office' column."""
    try:
        df = pd.read_csv(file_path)
        df['Office'] = df['Office'].str.strip()
        logger.info(f"Data read successfully from {file_path}")
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

    try:
        os.remove(file_path)
        logger.info(f"Removed processed file: {file_path}")
    except OSError as e:
        logger.error(f"Error removing file {file_path}: {e}")

    return excel_path


def generate_summary(file_path):
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook['License Counts']

    total_row = sheet.max_row
    summary = {
        'total_365_premium': sheet.cell(row=total_row, column=sheet.max_column - 4).value,
        'total_exchange': sheet.cell(row=total_row, column=sheet.max_column - 3).value,
        'total_cost': sheet.cell(row=total_row, column=sheet.max_column).value,
        'top_offices': []
    }

    # Get top 5 offices by total cost
    office_data = [(sheet.cell(row=i, column=1).value, sheet.cell(row=i, column=sheet.max_column).value)
                   for i in range(2, total_row)]
    office_data.sort(key=lambda x: x[1], reverse=True)
    summary['top_offices'] = office_data[:5]

    return summary
