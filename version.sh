#!/bin/bash
echo "{
  \"version\": \"$(git describe --tags --always --dirty)\",
  \"commit\": \"$(git rev-parse HEAD)\",
  \"date\": \"$(git show -s --format=%ci HEAD)\"
}" > version.json