# tests/test_data_generator.py

import csv
import random
import os

# List of sample offices, licenses, and names
offices = ['AION Management', 'AION Partners', 'New York Office', 'Chicago Office', 'Los Angeles Office',
           'Dallas Office', 'Houston Office', 'San Francisco Office', 'Seattle Office', 'Boston Office',
           'Miami Office', 'Phoenix Office', 'Atlanta Office', '', '']  # Include some blank offices

licenses = ['Microsoft 365 E3', 'Microsoft 365 Business Premium', 'Exchange Online (Plan 1)',
            'Exchange Online (Plan 2)', 'Microsoft 365 E5', 'Microsoft 365 F3', 'Microsoft 365 Business Basic',
            'Microsoft 365 Business Standard', 'Microsoft 365 A3 for faculty', 'Power BI Pro', 'Project Plan 3']

first_names = ['John', 'Jane', 'Alice', 'Bob', 'Charlie', 'David', 'Eva', 'Frank', 'Grace', 'Henry',
               'Ivy', 'Jack', 'Kelly', 'Liam', 'Mia', 'Noah', 'Olivia', 'Peter', 'Quinn', 'Rachel']

last_names = ['Doe', 'Smith', 'Johnson', 'Williams', 'Brown', 'Miller', 'Garcia', 'Wilson', 'Lee',
              'Taylor', 'Chen', 'White', 'Rodriguez', 'Martinez', 'Davis', 'Anderson', 'Thomas', 'Jackson', 'Martin']


def generate_user():
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    display_name = f"{first_name} {last_name}"
    user_principal_name = f"{first_name.lower()}.{last_name.lower()}@aion.com"
    office = random.choice(offices)
    license_count = random.randint(1, 3)
    user_licenses = '+'.join(random.sample(licenses, license_count))
    return [display_name, user_principal_name, office, user_licenses]


def generate_csv(filename, num_rows):
    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Display name', 'User principal name', 'Office', 'Licenses'])

        for _ in range(num_rows):
            csvwriter.writerow(generate_user())

    return filename


def generate_test_csv(tmp_path, num_rows=100):
    csv_file = tmp_path / "test_data.csv"
    return generate_csv(str(csv_file), num_rows)
