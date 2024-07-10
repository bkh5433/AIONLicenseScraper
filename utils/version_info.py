import os
import json


def get_version_info():
    """
        Retrieve version information from environment variables or version.json file.

        Returns:
            dict: A dictionary containing version information with keys:
                  version, branch, date, build, and environment.
        """

    # First, try to get version info from environment variables
    version = os.environ.get('APP_VERSION')
    branch = os.environ.get('APP_BRANCH')
    date = os.environ.get('APP_BUILD_DATE')
    build = os.environ.get('APP_BUILD')
    environment = os.environ.get('APP_ENVIRONMENT')

    # If any of the environment variables are not set, try to read from version.json
    if not all([version, branch, date, build, environment]):
        try:
            with open('version.json', 'r') as f:
                version_data = json.load(f)
                version = version_data.get('version', 'unknown')
                branch = version_data.get('branch', 'unknown')
                date = version_data.get('date', 'unknown')
                build = version_data.get('build', 'unknown')
                environment = version_data.get('environment', 'unknown')
        except FileNotFoundError:
            # If version.json doesn't exist, use default values
            version = version or 'unknown'
            branch = branch or 'unknown'
            date = date or 'unknown'
            build = build or 'unknown'
            environment = environment or 'unknown'

    return {
        "version": version,
        "branch": branch,
        "date": date,
        "build": build,
        "environment": environment
    }
