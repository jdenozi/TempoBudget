#!/bin/bash
# Hook: Check if n8n workflow was modified

# CLAUDE_FILE_PATHS contains the path of the file that was edited
if [ -n "$CLAUDE_FILE_PATHS" ]; then
    if echo "$CLAUDE_FILE_PATHS" | grep -q "n8n-workflows"; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "📦 Workflow n8n modifié !"
        echo "   Pense à synchroniser avec: ./scripts/n8n-sync.sh"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    fi
fi
