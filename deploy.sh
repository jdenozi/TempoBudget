#!/bin/bash

set -e

echo "=== Tempo Budget Deployment ==="

# Go to project directory
cd "$(dirname "$0")"

# Pull latest changes
echo "Pulling latest changes..."
git pull

# Get version from latest tag
VERSION=$(git describe --tags --always)
BUILD_DATE=$(date +%Y-%m-%d)

echo "Version: $VERSION"
echo "Build date: $BUILD_DATE"

# Export for docker-compose
export APP_VERSION=$VERSION
export BUILD_DATE=$BUILD_DATE

# Stop containers
echo "Stopping containers..."
docker-compose -f docker-compose.prod.yml down

# Rebuild images without cache
echo "Rebuilding images..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Start containers
echo "Starting containers..."
docker-compose -f docker-compose.prod.yml up -d

# Cleanup old images
echo "Cleaning up old images..."
docker image prune -f

echo "=== Deployment complete ==="
echo "Version $VERSION deployed successfully"
