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

echo "{
  \"version\": \"$(git describe --tags --always --dirty)\",
  \"branch\": \"$(git rev-parse --abbrev-ref HEAD)\",
  \"date\": \"$(git show -s --format=%ci HEAD)\",
  \"build\": \"$current_date.$new_build\",
  \"environment\": \"$environment\"
}" > version.json