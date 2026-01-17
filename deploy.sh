#!/bin/bash

set -e

echo "=== Tempo Budget Deployment ==="

# Go to project directory
cd "$(dirname "$0")"

# Get target (branch or tag), default to master
TARGET=${1:-master}

echo "Target: $TARGET"

# Fetch all remote changes
echo "Fetching remote changes..."
git fetch --all --tags

# Checkout target (branch or tag)
echo "Checking out $TARGET..."
if git rev-parse "refs/tags/$TARGET" >/dev/null 2>&1; then
    # It's a tag
    git checkout "tags/$TARGET"
elif git rev-parse "refs/remotes/origin/$TARGET" >/dev/null 2>&1; then
    # It's a branch
    git checkout "$TARGET"
    git pull origin "$TARGET"
else
    echo "Error: $TARGET is not a valid branch or tag"
    exit 1
fi

# Get version from latest tag or commit
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
