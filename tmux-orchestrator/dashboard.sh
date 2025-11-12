#!/bin/bash
# Dashboard for monitoring all agent windows

SESSION_NAME="${1:-semantic-layer}"

clear
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║        SEMANTIC LAYER SERVICE - TEAM DASHBOARD                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "🕐 $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Check if session exists
if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "❌ Session '$SESSION_NAME' not found"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 WINDOW STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get all windows
tmux list-windows -t "$SESSION_NAME" -F "#{window_index}|#{window_name}|#{window_panes}|#{window_active}" | while IFS='|' read -r idx name panes active; do
    if [ "$active" = "1" ]; then
        status="🟢 ACTIVE"
    else
        status="⚪ inactive"
    fi
    printf "Window %s: %-20s [%d panes] %s\n" "$idx" "$name" "$panes" "$status"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 AGENT ACTIVITY (Last 5 lines)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Backend PM
echo ""
echo "🔷 BACKEND PM (Window 2, Pane 0)"
tmux capture-pane -t "$SESSION_NAME:2.0" -p -S -5 2>/dev/null | tail -3 | sed 's/^/  │ /' || echo "  │ [Not responding]"

# Backend Dev
echo ""
echo "🔷 BACKEND DEV (Window 2, Pane 1)"
tmux capture-pane -t "$SESSION_NAME:2.1" -p -S -5 2>/dev/null | tail -3 | sed 's/^/  │ /' || echo "  │ [Not responding]"

# Frontend PM
echo ""
echo "🔶 FRONTEND PM (Window 3, Pane 0)"
tmux capture-pane -t "$SESSION_NAME:3.0" -p -S -5 2>/dev/null | tail -3 | sed 's/^/  │ /' || echo "  │ [Not responding]"

# Frontend Dev
echo ""
echo "🔶 FRONTEND DEV (Window 3, Pane 1)"
tmux capture-pane -t "$SESSION_NAME:3.1" -p -S -5 2>/dev/null | tail -3 | sed 's/^/  │ /' || echo "  │ [Not responding]"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 GIT STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Show git status
git -C "$(tmux display-message -t "$SESSION_NAME:0" -p '#{pane_current_path}')" status -sb 2>/dev/null || echo "Not a git repository"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 TIPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  • Switch windows: Ctrl+s then 1/2/3"
echo "  • Switch panes: Ctrl+s then arrow keys"
echo "  • Send message: ./tmux-orchestrator/send-claude-message.sh <target> \"message\""
echo "  • Targets: $SESSION_NAME:2.0 (Backend PM), $SESSION_NAME:2.1 (Backend Dev),"
echo "             $SESSION_NAME:3.0 (Frontend PM), $SESSION_NAME:3.1 (Frontend Dev)"
echo ""
