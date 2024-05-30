import pandas as pd
import os
from datetime import datetime
from create_app import app


def process_file(file_path):
    df = pd.read_csv(file_path)

    # Strip any leading/trailing whitespace in the 'Office' column
    df['Office'] = df['Office'].str.strip()

    # Create an empty dictionary to store the counts
    license_counts = {}

    # Specific licenses to look for
    target_licenses = {
        '365 Premium': ['Microsoft 365 Business Premium', 'E3'],
        'Exchange': ['Exchange']
    }

    # Initialize counts for each property and the 'Unaccounted' category
    for office in df['Office'].unique():
        if pd.isna(office) or office.strip() == '':
            continue
        office = office.strip()
        license_counts[office] = {key: 0 for key in target_licenses.keys()}

    # Add 'Unaccounted' category
    license_counts['Unaccounted'] = {key: 0 for key in target_licenses.keys()}

    # Initialize lists to log rows with empty 'Office' values and specific organizations
    unaccounted_log = []
    aion_management = []
    aion_partners = []
    other_properties = []

    # Iterate through each row in the DataFrame
    for index, row in df.iterrows():
        office = row['Office']
        licenses = row['Licenses']
        user_principal_name = row['User principal name']

        # Skip rows where 'Licenses' is NaN or empty
        if pd.isna(licenses) or licenses.strip() == '':
            continue

        # Split the licenses by '+' if multiple licenses are listed in one cell
        licenses_list = licenses.split('+')

        has_target_license = False
        for license in licenses_list:
            license = license.strip()

            for key, variants in target_licenses.items():
                if any(variant in license for variant in variants):
                    has_target_license = True
                    license_counts[office if not (pd.isna(office) or office.strip() == '') else 'Unaccounted'][key] += 1
                    if office == 'AION Management':
                        aion_management.append([row['Display name'], license, user_principal_name])
                    elif office == 'AION Partners':
                        aion_partners.append([row['Display name'], license, user_principal_name])
                    else:
                        other_properties.append([row['Display name'], license, user_principal_name, office])

        # Log users with no office but have a specific license
        if (pd.isna(office) or office.strip() == '') and has_target_license:
            unaccounted_log.append(f"{row['Display name']} ({user_principal_name})")

    # Convert the dictionary to a DataFrame for better visualization
    license_counts_df = pd.DataFrame.from_dict(license_counts, orient='index').fillna(0)

    # Calculate the totals and append them as a new row at the end of the DataFrame
    totals = license_counts_df.sum(axis=0).rename('Total')
    license_counts_df = pd.concat([license_counts_df, pd.DataFrame(totals).T])

    # Convert the lists to DataFrames for the new sheets
    aion_management_df = pd.DataFrame(aion_management, columns=['Display Name', 'License Type', 'User Principal Name'])
    aion_partners_df = pd.DataFrame(aion_partners, columns=['Display Name', 'License Type', 'User Principal Name'])
    other_properties_df = pd.DataFrame(other_properties,
                                       columns=['Display Name', 'License Type', 'User Principal Name', 'Office'])

    # Save the results to a new Excel file with formatting
    current_date = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    excel_path = os.path.join(app.config['OUTPUT_FOLDER'], f"license_counts_{current_date}.xlsx")
    with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
        license_counts_df.to_excel(writer, sheet_name='License Counts')
        aion_management_df.to_excel(writer, sheet_name='AION Management', index=False)
        aion_partners_df.to_excel(writer, sheet_name='AION Partners', index=False)
        other_properties_df.to_excel(writer, sheet_name='Other Properties', index=False)

        workbook = writer.book

        # Define formatting
        header_format = workbook.add_format(
            {'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#D7E4BC', 'border': 1})
        total_format = workbook.add_format({'bold': True, 'fg_color': '#FFEB9C', 'border': 1})

        def format_sheet(worksheet, df, is_totals=False):
            # Write the column headers with the defined format
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num + 1 if is_totals else col_num, value, header_format)
            if is_totals:
                worksheet.write(0, 0, 'Office', header_format)

            # Set column widths
            for col_num, col in enumerate(df.columns):
                column_len = df[col].astype(str).str.len().max()
                column_len = max(column_len, len(col)) + 2
                worksheet.set_column(col_num + (1 if is_totals else 0), col_num + (1 if is_totals else 0), column_len)
            if is_totals:
                worksheet.set_column(0, 0, max(df.index.astype(str).str.len().max(), len('Office')) + 2)

            # Apply autofilter
            worksheet.autofilter(0, 0, len(df), len(df.columns) + (1 if is_totals else 0) - 1)

        # Format License Counts sheet
        license_counts_worksheet = writer.sheets['License Counts']
        format_sheet(license_counts_worksheet, license_counts_df, is_totals=True)
        # Format totals row
        for col_num in range(len(license_counts_df.columns)):
            license_counts_worksheet.write(len(license_counts_df), col_num + 1, license_counts_df.iloc[-1, col_num],
                                           total_format)
        license_counts_worksheet.write(len(license_counts_df), 0, 'Total', total_format)

        # Format AION Management sheet
        aion_management_worksheet = writer.sheets['AION Management']
        format_sheet(aion_management_worksheet, aion_management_df)

        # Format AION Partners sheet
        aion_partners_worksheet = writer.sheets['AION Partners']
        format_sheet(aion_partners_worksheet, aion_partners_df)

        # Format Other Properties sheet
        other_properties_worksheet = writer.sheets['Other Properties']
        format_sheet(other_properties_worksheet, other_properties_df)

    os.remove(file_path)  # Remove the uploaded file after processing
    return excel_path
