#!/bin/bash

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

# Export the variables
export VERSION
export BRANCH
export BUILD_DATE
export BUILD
export DEPLOY_ENV="$environment"

# Print the information
echo "Building with:"
echo "VERSION: $VERSION"
echo "BRANCH: $BRANCH"
echo "BUILD_DATE: $BUILD_DATE"
echo "BUILD: $BUILD"
echo "ENVIRONMENT: $environment"

echo "{
  \"version\": \"$VERSION\",
  \"branch\": \"$BRANCH\",
  \"date\": \"$BUILD_DATE\",
  \"build\": \"$BUILD\",
  \"environment\": \"$environment\"
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

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --rebuild) REBUILD=true ;;
        --prune) PRUNE=true ;;
        *) break ;;
    esac
    shift
done

if [ "$PRUNE" = true ]; then
    echo "Pruning dangling images..."
    docker image prune -f
fi

if [ "$REBUILD" = true ]; then
    echo "Rebuilding Docker images..."
    docker-compose build --no-cache
fi

echo "Starting or updating containers..."
docker-compose up -d --build

echo "Operation completed."