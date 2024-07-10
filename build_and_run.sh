#!/bin/bash

# build_and_run.sh
#
# This script manages the build and deployment process for the AION License Count application.
# It performs the following tasks:
# 1. Generates and updates build information
# 2. Creates a version.json file with build details
# 3. Stops and removes existing Docker containers
# 4. Optionally prunes Docker images and rebuilds containers
# 5. Starts or updates the Docker containers
#
# Usage: ./build_and_run.sh [--rebuild] [--prune]
#   --rebuild: Force rebuild of Docker images
#   --prune: Prune dangling Docker images before building

# Get the current date in YYYYMMDD format
current_date=$(date +%Y%m%d)

# Read the last build number (if it exists)
build_file=".last_build_number"
if [ -f "$build_file" ]; then
    last_build=$(cat "$build_file")
else
    last_build=0
fi

# Increment the build number
new_build=$((last_build + 1))

# Save the new build number
echo $new_build > "$build_file"

# Get the environment (default to 'dev' if not set)
environment=${DEPLOY_ENV:-dev}

# Fetch git information and assign to variables
VERSION=$(git describe --tags --always --dirty)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
BUILD_DATE=$(TZ=EST5EDT date +"%Y-%m-%dT%H:%M")
BUILD="$current_date.$new_build"
SECRET_KEY=$(python -c "import os; print(os.urandom(24).hex())")

# Export the variables
export VERSION
export BRANCH
export BUILD_DATE
export BUILD
export DEPLOY_ENV="$environment"
export FLASK_SECRET_KEY="$SECRET_KEY"

# Print the information
echo "Building with:"
echo "VERSION: $VERSION"
echo "BRANCH: $BRANCH"
echo "BUILD_DATE: $BUILD_DATE"
echo "BUILD: $BUILD"
echo "ENVIRONMENT: $environment"
echo "FLASK_SECRET_KEY: $SECRET_KEY"

# Create version.json file
echo "{
  \"version\": \"$VERSION\",
  \"branch\": \"$BRANCH\",
  \"date\": \"$BUILD_DATE\",
  \"build\": \"$BUILD\",
  \"environment\": \"$environment\",
  \"secret_key\": \"$SECRET_KEY\"

}" > version.json

# Parse command line arguments
REBUILD=false
PRUNE=false

echo "Stopping and removing existing containers..."
if docker-compose ps -q | grep -q .; then
    docker-compose down -v
    echo "Containers stopped and removed."
else
    echo "No running containers found."
fi

# Process command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --rebuild) REBUILD=true ;;
        --prune) PRUNE=true ;;
        *) break ;;
    esac
    shift
done

# Prune Docker images if requested
if [ "$PRUNE" = true ]; then
    echo "Pruning dangling images..."
    docker image prune -f
fi

# Rebuild Docker images if requested
if [ "$REBUILD" = true ]; then
    echo "Rebuilding Docker images..."
    docker-compose build --no-cache
fi

echo "Starting or updating containers..."
docker-compose up -d --build

echo "Operation completed."