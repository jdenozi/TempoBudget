#!/bin/bash
# Synchronize n8n workflow templates with the n8n instance
# Usage: ./n8n-sync.sh [workflow-name] [--list] [--activate]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WORKFLOWS_DIR="$PROJECT_ROOT/n8n-workflows"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# Check required env vars
if [ -z "$N8N_URL" ]; then
    echo "Error: N8N_URL environment variable is not set"
    exit 1
fi

if [ -z "$N8N_API_KEY" ]; then
    echo "Error: N8N_API_KEY environment variable is not set"
    exit 1
fi

# Remove trailing slash from URL
N8N_URL="${N8N_URL%/}"

# Parse arguments
LIST_ONLY=false
ACTIVATE=false
WORKFLOW_FILTER=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --list)
            LIST_ONLY=true
            shift
            ;;
        --activate)
            ACTIVATE=true
            shift
            ;;
        *)
            WORKFLOW_FILTER="$1"
            shift
            ;;
    esac
done

# Function to make n8n API calls
n8n_api() {
    local method="$1"
    local endpoint="$2"
    local data="$3"

    if [ -n "$data" ]; then
        curl -s -X "$method" "${N8N_URL}/api/v1${endpoint}" \
            -H "X-N8N-API-KEY: ${N8N_API_KEY}" \
            -H "Content-Type: application/json" \
            -d "$data"
    else
        curl -s -X "$method" "${N8N_URL}/api/v1${endpoint}" \
            -H "X-N8N-API-KEY: ${N8N_API_KEY}"
    fi
}

# Test connection
echo "Connecting to n8n at $N8N_URL..."
if ! n8n_api GET "/workflows" > /dev/null 2>&1; then
    echo "Error: Cannot connect to n8n. Check N8N_URL and N8N_API_KEY."
    exit 1
fi
echo "Connected successfully."
echo ""

# List local workflows
echo "Local workflows in $WORKFLOWS_DIR:"
for f in "$WORKFLOWS_DIR"/*.json; do
    if [ -f "$f" ]; then
        name=$(jq -r '.name // "unnamed"' "$f")
        echo "  - $(basename "$f"): $name"
    fi
done
echo ""

if [ "$LIST_ONLY" = true ]; then
    echo "Remote workflows in n8n:"
    n8n_api GET "/workflows" | jq -r '.data[] | "  - \(.id): \(.name) [\(if .active then "active" else "inactive" end)]"'
    exit 0
fi

# Sync workflows
echo "Syncing workflows..."

for f in "$WORKFLOWS_DIR"/*.json; do
    if [ ! -f "$f" ]; then
        continue
    fi

    filename=$(basename "$f")

    # Apply filter if specified
    if [ -n "$WORKFLOW_FILTER" ] && [[ "$filename" != *"$WORKFLOW_FILTER"* ]]; then
        continue
    fi

    workflow_name=$(jq -r '.name // "unnamed"' "$f")
    echo ""
    echo "Processing: $workflow_name ($filename)"

    # Check if workflow exists by name
    existing=$(n8n_api GET "/workflows" | jq -r --arg name "$workflow_name" '.data[] | select(.name == $name) | .id')

    if [ -n "$existing" ]; then
        echo "  Workflow exists with ID: $existing"
        echo "  Updating..."

        # Update workflow
        result=$(n8n_api PUT "/workflows/$existing" "$(cat "$f")")

        if echo "$result" | jq -e '.id' > /dev/null 2>&1; then
            echo "  Updated successfully."
        else
            echo "  Error updating: $(echo "$result" | jq -r '.message // "Unknown error"')"
            continue
        fi
    else
        echo "  Workflow does not exist. Creating..."

        # Create workflow
        result=$(n8n_api POST "/workflows" "$(cat "$f")")

        if echo "$result" | jq -e '.id' > /dev/null 2>&1; then
            existing=$(echo "$result" | jq -r '.id')
            echo "  Created with ID: $existing"
        else
            echo "  Error creating: $(echo "$result" | jq -r '.message // "Unknown error"')"
            continue
        fi
    fi

    # Activate if requested
    if [ "$ACTIVATE" = true ]; then
        echo "  Activating..."
        result=$(n8n_api POST "/workflows/$existing/activate")
        if echo "$result" | jq -e '.active' > /dev/null 2>&1; then
            echo "  Activated."
        else
            echo "  Could not activate: $(echo "$result" | jq -r '.message // "Unknown error"')"
        fi
    fi
done

echo ""
echo "Sync complete."
