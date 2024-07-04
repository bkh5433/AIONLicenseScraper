#!/bin/bash

# Declare variables
VERSION=""
BRANCH=""
BUILD_DATE=""

# Fetch git information and assign to variables
VERSION=$(git describe --tags --always --dirty)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
BUILD_DATE=$(TZ=EST5EDT date +"%Y-%m-%dT%H:%M")

# Export the variables
export VERSION
export BRANCH
export BUILD_DATE

# Print the information
echo "Building with:"
echo "VERSION: $VERSION"
echo "BRANCH: $BRANCH"
echo "BUILD_DATE: $BUILD_DATE"

# Parse command line arguments
REBUILD=false
PRUNE=false

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