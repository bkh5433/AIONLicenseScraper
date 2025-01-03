![AION Microsoft License Counter](static/images/screenshot2.png)

# AION Microsoft License Report

AION Microsoft License Counter is a web application that allows users to upload a CSV file exported from Azure to generate a report of the number of Microsoft licenses in use.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
   - [Environment Variables](#environment-variables)
- [Deployment](#deployment)
   - [Using Docker Compose](#using-docker-compose)
   - [Using the Build and Run Script](#using-the-build-and-run-script)
   - [Customizing Nginx Configuration](#customizing-nginx-configuration)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Features

- **CSV Upload**: Easily upload CSV files exported from Azure.
- **Report Generation**: Generate detailed reports on Microsoft licenses in use.
- **Secure Deployment**: Utilize Docker and Nginx for secure and scalable deployments.
- **Admin Center**: Monitor metrics and manage the application through the admin interface.
- **Error Handling**: Comprehensive error pages with animations for better user experience.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- **Docker**: Ensure Docker is installed on your machine. You can download it
  from [here](https://www.docker.com/get-started).
- **Docker Compose**: Make sure Docker Compose is installed. Installation instructions can be
  found [here](https://docs.docker.com/compose/install/).
- **Git**: Git should be installed to clone the repository. Download it from [here](https://git-scm.com/downloads).
- **OpenSSL**: Required for generating secret keys. Install it via your package manager if not already available.

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/aion-license-counter.git
   cd aion-license-counter
   ```

2. **Environment Variables**

   The `build_and_run.sh` script automatically generates and manages environment variables:

   - `VERSION`: Determined from git tags (e.g., "1.0.0-dirty")
   - `BRANCH`: Current git branch
   - `BUILD_DATE`: Current date and time in EST
   - `BUILD`: Build number in format YYYYMMDD.increment
   - `DEPLOY_ENV`: Deployment environment (defaults to "dev")
   - `FLASK_SECRET_KEY`: Randomly generated secret key

   These variables are:

   - Exported as environment variables
   - Saved to `version.json`
   - Passed to Docker during build

   No manual `.env` file creation is required, but you can override `DEPLOY_ENV` by setting it before running the
   script:

   ```bash
   export DEPLOY_ENV=production
   ./build_and_run.sh
   ```

## Deployment

You can deploy the AION Microsoft License Counter application using Docker Compose or the provided build and run script.

### Using Docker Compose

1. **Build and Start the Containers**

   Use the following command to build the Docker images and start the containers:

   ```bash
   docker-compose up --build -d
   ```

   This command performs the following:

   - Builds the Docker images based on the `Dockerfile` and `Dockerfile.nginx`.
   - Starts the `web` and `nginx` services in detached mode.

2. **Access the Application**

   Once the containers are running, navigate to `http://localhost` in your web browser to access the application.

3. **Managing Containers**

   - **Stop Containers**

     ```bash
     docker-compose down
     ```

   - **View Logs**

     ```bash
     docker-compose logs -f
     ```

### Using the Build and Run Script

The `build_and_run.sh` script automates the build and deployment process. It handles versioning, builds the Docker
images, and starts the containers.

1. **Make the Script Executable**

   ```bash
   chmod +x build_and_run.sh
   ```

2. **Run the Script**

   ```bash
   ./build_and_run.sh
   ```

   **Optional Flags:**

   - `--rebuild`: Force rebuild of Docker images.
   - `--prune`: Prune dangling Docker images before building.

   **Example with Flags:**

   ```bash
   ./build_and_run.sh --rebuild --prune
   ```

3. **What the Script Does**

   - **Generates Build Information**: Creates or updates the `version.json` file with build details.
   - **Manages Environment Variables**: Automatically generates environment variables and exports them.
   - **Manages Docker Containers**: Stops and removes existing containers if they are running.
   - **Prunes Docker Images**: Removes dangling images to free up space (optional).
   - **Builds Docker Images**: Rebuilds the images without using the cache (optional).
   - **Starts Containers**: Launches the services defined in `docker-compose.yml`.

4. **Environment Variable Management**

   The `build_and_run.sh` script handles the creation and management of environment variables automatically. It performs
   the following:

   - **Generates a Secret Key**: Uses OpenSSL to generate a random secret key.
   - **Creates `version.json`**: Stores build details such as version, branch, build date, build number, environment,
     and secret key.
   - **Passes Variables to Docker**: These variables are exported and used during the Docker build process.

   **Note:** If you wish to override the deployment environment, set the `DEPLOY_ENV` variable before running the
   script:

   ```bash
   export DEPLOY_ENV=production
   ./build_and_run.sh
   ```

5. **Access the Application**

   After running the script, access the application at `http://localhost`.

### Customizing Nginx Configuration

Depending on your deployment environment, you might need to customize the Nginx configuration to suit your specific
requirements. Common adjustments include:

- **Server Name**: Update the `server_name` in `nginx.conf` to match your domain or server IP.

  ```nginx
  server {
      listen 80;
      server_name yourdomain.com;

      # Redirect all HTTP requests to HTTPS
      return 301 https://$server_name$request_uri;
  }

  server {
      listen 443 ssl;
      server_name yourdomain.com;

      # SSL certificate configuration
      ssl_certificate /etc/nginx/ssl/yourdomain.crt;
      ssl_certificate_key /etc/nginx/ssl/yourdomain.key;

      # ... rest of the configuration
  }
  ```

- **SSL Certificates**: Replace the self-signed certificates with your official SSL certificates for production
  environments.

   - Place your `.crt` and `.key` files in the `ssl/` directory.
   - Update the `ssl_certificate` and `ssl_certificate_key` paths in `nginx.conf` accordingly.

- **Proxy Settings**: If your Flask application runs on a different port or requires additional proxy headers, update
  the `location /` block in `nginx.conf`.

- **Static Files**: Ensure that the paths for static and upload directories in the `alias` directives match your
  application's structure.

After making changes to `nginx.conf`, rebuild and restart the Nginx container to apply the new configuration:

```bash
docker-compose build nginx
docker-compose up -d nginx
```

## Usage

1. **Upload CSV File**

   - Navigate to the application's upload page.
   - Drag and drop your CSV file exported from Azure or click to select the file.
   - Enter the **Cost per 365 Premium User** and **Cost per Exchange License**.
   - Click **Generate** to create the license report.

2. **View Summary**

   After processing, you'll be redirected to the summary page where you can:

   - View detailed charts and metrics.
   - Download the full report.
   - Reset metrics if necessary.

3. **Admin Center**

   - Access the admin center at `http://localhost/admin`.
   - Monitor unique users, reports generated, and view application logs.
   - Reset metrics or filter logs as needed.

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

1. **Fork the Repository**

2. **Create a Feature Branch**

   ```bash
   git checkout -b feature/YourFeature
   ```

3. **Commit Your Changes**

   ```bash
   git commit -m "Add Your Feature"
   ```

4. **Push to the Branch**

   ```bash
   git push origin feature/YourFeature
   ```

5. **Create a Pull Request**

## License

This project is licensed under the [MIT License](LICENSE).

## Security Measures

Ensuring the security of file uploads and data handling is paramount for the AION Microsoft License Counter application.
The application implements several security measures within `app.py` and `csv_parser.py` to safeguard against common
vulnerabilities.

### Security Measures in `app.py`

#### 1. **Authentication and Authorization**

- **Flask-Login Integration**:
    - **Implementation**: Utilizes `Flask-Login` to manage user sessions, ensuring that only authenticated users can
      access certain routes like the admin center.
    - **Benefit**: Prevents unauthorized access to sensitive parts of the application.

  ```python
  from flask_login import LoginManager, login_user, login_required, logout_user, current_user
  ```

- **User Loader Function**:
    - **Implementation**: Defines a `user_loader` callback to load user information from the database.
    - **Benefit**: Ensures that only valid users can be authenticated and maintain active sessions.

  ```python
  @login_manager.user_loader
  def load_user(user_id):
      user_doc = db().collection('users').document(user_id).get()
      if user_doc.exists:
          return User(user_id)
      return None
  ```

#### 2. **File Upload Restrictions**

- **Allowed File Extensions**:
    - **Implementation**: The `allowed_file` function restricts uploads to only `.csv` files.
    - **Benefit**: Minimizes the risk of malicious files being uploaded and executed on the server.

  ```python
  def allowed_file(filename):
      return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
  ```

#### 3. **Input Validation**

- **CSV File Validation**:
    - **Implementation**: Utilizes the `validate_csv` function to ensure that the uploaded CSV meets expected criteria
      before processing.
    - **Benefit**: Prevents malformed or malicious CSV data from being processed, which could lead to security breaches
      or application crashes.

  ```python
  is_valid, error_message = validate_csv(file_path)
  if not is_valid:
      invalid_path = os.path.join(app.config['INVALID_FOLDER'], file.filename)
      os.rename(file_path, invalid_path)
      logger.error(f"File validation failed: {file.filename} - {error_message}")
      return render_template('error.html',
                             error_title='Invalid CSV File',
                             error_message=error_message)
  ```

#### 4. **Secure Session Management**

- **Secret Key Handling**:
    - **Implementation**: The application fetches a secret key from `version.json` or generates a secure random key if
      not available.
    - **Benefit**: Ensures that session data is securely signed to prevent tampering.

  ```python
  try:
      with open('version.json', 'r') as f:
          version_info = json.load(f)
      app.secret_key = version_info.get('secret_key') or os.urandom(24).hex()
  except (FileNotFoundError, json.JSONDecodeError):
      app.secret_key = os.urandom(24).hex()
  ```

#### 5. **Error Handling and Logging**

- **Custom Error Handlers**:
    - **Implementation**: Defines custom handlers for specific HTTP errors like 404 and general exceptions.
    - **Benefit**: Provides controlled feedback to users without exposing sensitive stack traces or server information.

  ```python
  @app.errorhandler(404)
  def page_not_found(e):
      logger.warning(f"Page not found {e}")
      return render_template('404.html'), 404
  ```

- **Comprehensive Logging**:
    - **Implementation**: Logs essential events, errors, and request lifecycle stages to monitor and debug the
      application effectively.
    - **Benefit**: Helps in identifying and responding to security incidents promptly.

  ```python
  @app.before_request
  def log_request_start():
      logger.info(f"Start processing request: {request.method} {request.path}")

  @app.after_request
  def log_request_end(response):
      logger.info(f"End processing request: {request.method} {request.path} with status {response.status}")
      return response
  ```

#### 6. **Secure Data Handling**

- **Session Management**:
    - **Implementation**: Uses server-side sessions to manage user states securely.
    - **Benefit**: Reduces the risk of client-side manipulation of session data.

  ```python
  from flask import session
  ```

#### 7. **HTTPS Enforcement**

- **Nginx Configuration for SSL**:
    - **Implementation**: The Nginx server is configured to redirect HTTP traffic to HTTPS and handle SSL termination.
    - **Benefit**: Encrypts data in transit, protecting sensitive information from eavesdropping and man-in-the-middle
      attacks.

  ```nginx
  # Redirect all HTTP requests to HTTPS
  server {
      listen 80;
      server_name localhost;

      return 301 https://$server_name$request_uri;
  }

  # HTTPS Server Block
  server {
      listen 443 ssl;
      server_name localhost;

      ssl_certificate /etc/nginx/ssl/selfsigned.crt;
      ssl_certificate_key /etc/nginx/ssl/selfsigned.key;
      
      # ... additional SSL settings ...
  }
  ```

### Security Measures in `csv_parser.py`

#### 1. **Input Sanitization and Validation**

- **Reading and Cleaning Data**:
    - **Implementation**: Strips whitespaces and ensures necessary columns are present before processing.
    - **Benefit**: Prevents injection attacks and ensures that the data conforms to expected formats.

  ```python
  def read_and_prepare_data(file_path):
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
  ```

#### 2. **Secure File Handling**

- **Temporary File Management**:
    - **Implementation**: Processes files in designated directories and removes them after processing.
    - **Benefit**: Minimizes the risk of leftover temporary files that could be exploited.

  ```python
  def process_file(file_path, cost_per_user=115, cost_per_exchange=20):
      # ... processing logic ...
      try:
          os.remove(file_path)
          logger.info(f"Removed uploaded file: {file_path}")
      except OSError as e:
          logger.error(f"Error removing uploaded {file_path}: {e}")
  ```

#### 3. **Exception Handling**

- **Robust Error Handling**:
    - **Implementation**: Catches and logs specific exceptions like `PermissionError` and general exceptions during file
      processing and saving.
    - **Benefit**: Prevents the application from crashing due to unexpected errors and ensures that issues are logged
      for further investigation.

  ```python
  def save_to_excel(...):
      try:
          # ... saving logic ...
          logger.info(f"Data saved to Excel file: {excel_path}")
      except PermissionError:
          logger.error(f"Permission denied when writing to {excel_path}")
      except Exception as e:
          logger.error(f"Error writing to Excel file {excel_path}: {e}")
  ```

#### 4. **Resource Management**

- **Optimized Data Processing**:
    - **Implementation**: Utilizes pandas and openpyxl efficiently to handle large datasets.
    - **Benefit**: Reduces the risk of resource exhaustion attacks by ensuring that data is processed optimally.

#### 5. **Unique File Naming**

- **UUID for File Identification**:
    - **Implementation**: Generates unique filenames using UUIDs to prevent filename collisions and directory traversal
      attacks.
    - **Benefit**: Ensures that each processed file has a unique identifier, mitigating risks associated with
      predictable filenames.

  ```python
  def process_file(file_path, cost_per_user=115, cost_per_exchange=20):
      # ... processing logic ...
      file_id = str(uuid.uuid4())
      internal_filename = f"{file_id}_license_counts_{current_date}.xlsx"
  ```

#### 6. **Data Integrity Checks**

- **Validation Before Processing**:
    - **Implementation**: Ensures that the CSV contains the necessary columns and that data types are correct before
      proceeding.
    - **Benefit**: Maintains data integrity and prevents errors during report generation.

#### 7. **Logging and Monitoring**

- **Comprehensive Logging**:
    - **Implementation**: Logs every significant step of the CSV processing pipeline, including successes and failures.
    - **Benefit**: Facilitates monitoring and quick identification of potential security issues or data inconsistencies.

  ```python
  def process_file(...):
      logger.info(f"Processing file: {file_path}")
      # ... processing steps ...
      logger.info(f"Processed file saved to: {excel_path}")
  ```


    

