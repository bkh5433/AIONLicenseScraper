# Dockerfile for AION License Count application

# Use Python 3.12.3 with Alpine 3.20 as the base image
FROM python:3.12.3-bullseye


# Set the working directory in the container
WORKDIR /app

# Install build dependencies
#RUN apk add --no-cache gcc g++ python3-dev musl-dev linux-headers

# Copy the requirements file into the container
COPY requirements.txt .


# Install the Python dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set build arguments and pass them as environment variables
# These are used to provide version and build information to the application
ARG VERSION=unknown
ARG BRANCH=unknown
ARG BUILD_DATE=unknown
ARG BUILD=unknown
ARG DEPLOY_ENV=unknown

ENV APP_VERSION=$VERSION
ENV APP_BRANCH=$BRANCH
ENV APP_BUILD_DATE=$BUILD_DATE
ENV APP_BUILD=$BUILD
ENV APP_ENVIRONMENT=$DEPLOY_ENV




# Set environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0


# Command to run the application using Gunicorn
# -w 4: Use 4 worker processes
# -b 0.0.0.0:5000: Bind to all interfaces on port 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]

