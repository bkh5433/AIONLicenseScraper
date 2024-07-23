"""
CSV validation module for the AION License Count application.

This module provides functionality to validate the structure of uploaded CSV files,
ensuring they contain the required columns for license counting.
"""

import pandas as pd

# Define the required columns for the CSV file
REQUIRED_COLUMNS = ['Office', 'Licenses', 'User principal name', 'Display name']


def validate_csv(file_path):
    """
       Validate the CSV file to ensure it has the required columns.

       This function reads the CSV file and checks if it contains all the required columns
       defined in the REQUIRED_COLUMNS list. It also catches potential errors that might
       occur during the file reading process.

       Args:
           file_path (str): The path to the CSV file to be validated.

       Returns:
           tuple: A tuple containing:
               - bool: True if the file is valid, False otherwise.
               - str or None: An error message if the file is invalid, None otherwise.

       Raises:
           No exceptions are raised; all are caught and returned as error messages.
       """
    try:
        # Attempt to read the CSV file
        df = pd.read_csv(file_path)

        # Check for missing columns
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            return False, f"Missing columns: {', '.join(missing_columns)}"

        # If we've made it this far, the file is valid
        return True, None
    except pd.errors.ParserError:
        # Handle CSV parsing errors (e.g., malformed CSV)
        return False, "Invalid CSV file format."
    except Exception as e:
        # Catch any other unexpected errors
        return False, str(e)
