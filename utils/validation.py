import pandas as pd

REQUIRED_COLUMNS = ['Office', 'Licenses', 'User principal name', 'Display name']


def validate_csv(file_path):
    """Validate the CSV file to ensure it has the required columns."""
    try:
        df = pd.read_csv(file_path)
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            return False, f"Missing columns: {', '.join(missing_columns)}"
        return True, None
    except pd.errors.ParserError:
        return False, "Invalid CSV file format."
    except Exception as e:
        return False, str(e)
