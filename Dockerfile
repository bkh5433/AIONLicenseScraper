FROM python:3.12.3-alpine3.20


# Set the working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Set build arguments and pass them as environment variables
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




# env variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0


# Run the application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]

