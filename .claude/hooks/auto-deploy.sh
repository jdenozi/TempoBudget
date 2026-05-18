#!/bin/bash
# Hook: Auto-deploy after git tag

# Check if the command was a git tag
if [ -n "$CLAUDE_TOOL_RESULT" ]; then
    # Check if the result mentions a new tag being pushed
    if echo "$CLAUDE_TOOL_RESULT" | grep -q "\[new tag\]"; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🚀 Nouveau tag détecté ! Lancement du déploiement..."
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        # Run deploy script
        if [ -x "/home/debian/TempoBudget/deploy.sh" ]; then
            cd /home/debian/TempoBudget && ./deploy.sh
        else
            echo "⚠️  Script deploy.sh non trouvé ou non exécutable"
            echo "   Déploiement manuel requis: ./deploy.sh"
        fi
    fi
fi
