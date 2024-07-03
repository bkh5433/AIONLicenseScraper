#!/bin/bash
echo "{
  \"version\": \"$(git describe --tags --always --dirty)\",
  \"branch\": \"$(git rev-parse --abbrev-ref HEAD)\",
  \"date\": \"$(git show -s --format=%ci HEAD)\"
}" > version.json