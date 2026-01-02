#!/bin/bash

set -e

echo "=== Tempo Budget Deployment ==="

# Go to project directory
cd "$(dirname "$0")"

# Get target (branch or tag), default to master
TARGET=${1:-master}

echo "Target: $TARGET"

# Reset any local changes
echo "Resetting local changes..."
git reset --hard HEAD
git clean -fd

# Fetch all remote changes (force update tags)
echo "Fetching remote changes..."
git fetch --all --tags --force

# Checkout target
echo "Checking out $TARGET..."
if git rev-parse "refs/tags/$TARGET" >/dev/null 2>&1; then
    # It's a tag
    echo "Deploying tag $TARGET"
    git checkout "tags/$TARGET" --force
elif git rev-parse "refs/remotes/origin/$TARGET" >/dev/null 2>&1; then
    # It's a branch
    echo "Deploying branch $TARGET"
    git checkout "$TARGET" --force
    git reset --hard "origin/$TARGET"
else
    echo "Error: $TARGET is not a valid branch or tag"
    exit 1
fi

# Show current commit
echo "Current commit:"
git log --oneline -1

# Get version
VERSION=$(git describe --tags --always)
BUILD_DATE=$(date +%Y-%m-%d)

echo "Version: $VERSION"
echo "Build date: $BUILD_DATE"

# Export for docker-compose
export APP_VERSION=$VERSION
export BUILD_DATE=$BUILD_DATE

# Stop and remove containers
echo "Stopping containers..."
docker-compose -f docker-compose.prod.yml down --remove-orphans

# Remove old images to force rebuild
echo "Removing old images..."
docker-compose -f docker-compose.prod.yml rm -f
docker image rm -f $(docker images -q 'tempo*' 2>/dev/null) 2>/dev/null || true

# Rebuild images without cache
echo "Rebuilding images..."
docker-compose -f docker-compose.prod.yml build --no-cache --pull

# Start containers
echo "Starting containers..."
docker-compose -f docker-compose.prod.yml up -d

# Cleanup
echo "Cleaning up..."
docker image prune -f
docker system prune -f --volumes 2>/dev/null || true

echo ""
echo "=== Deployment complete ==="
echo "Version $VERSION deployed successfully"
echo "Commit: $(git log --oneline -1)"
