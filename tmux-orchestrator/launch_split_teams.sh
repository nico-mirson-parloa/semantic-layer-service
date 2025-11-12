#!/bin/bash
# Launch split-window team setup for semantic-layer-service
# This creates a split-window layout with dashboard

set -e

SESSION_NAME="${1:-semantic-layer}"
PROJECT_DIR="${2:-$(pwd)}"

echo "=== Launching Split Team Setup ==="
echo "Session: $SESSION_NAME"
echo "Project: $PROJECT_DIR"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if session exists
if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Creating new tmux session: $SESSION_NAME"
    tmux new-session -d -s "$SESSION_NAME" -c "$PROJECT_DIR"
fi

# Window 0: Dashboard (top) + Orchestrator (bottom)
echo "Setting up Window 0: Dashboard + Orchestrator..."
tmux rename-window -t "$SESSION_NAME:0" "Dashboard"
tmux send-keys -t "$SESSION_NAME:0" "cd '$PROJECT_DIR'" Enter
# Use a while loop instead of watch (macOS doesn't have watch by default)
tmux send-keys -t "$SESSION_NAME:0" "while true; do clear; '$SCRIPT_DIR/dashboard.sh' '$SESSION_NAME'; sleep 5; done" Enter

# Split for orchestrator at bottom (20% height)
tmux split-window -t "$SESSION_NAME:0" -v -p 20 -c "$PROJECT_DIR"
tmux send-keys -t "$SESSION_NAME:0.1" "cd '$PROJECT_DIR'" Enter
tmux send-keys -t "$SESSION_NAME:0.1" "echo '=== Orchestrator ===' && echo 'Starting Claude...'" Enter
tmux send-keys -t "$SESSION_NAME:0.1" "claude --dangerously-skip-permissions" Enter

# Window 1: Backend Team (PM top, Dev bottom)
echo "Setting up Window 1: Backend Team..."
tmux new-window -t "$SESSION_NAME:1" -n "Backend" -c "$PROJECT_DIR"
tmux send-keys -t "$SESSION_NAME:1" "cd '$PROJECT_DIR'" Enter
tmux send-keys -t "$SESSION_NAME:1" "echo '=== Backend PM ===' && echo 'Starting Claude...'" Enter
tmux send-keys -t "$SESSION_NAME:1" "claude --dangerously-skip-permissions" Enter

# Split for backend developer (50% height)
sleep 2
tmux split-window -t "$SESSION_NAME:1" -v -p 50 -c "$PROJECT_DIR"
tmux send-keys -t "$SESSION_NAME:1.1" "cd '$PROJECT_DIR'" Enter
tmux send-keys -t "$SESSION_NAME:1.1" "echo '=== Backend Developer ===' && echo 'Starting Claude...'" Enter
tmux send-keys -t "$SESSION_NAME:1.1" "claude --dangerously-skip-permissions" Enter

# Window 2: Frontend Team (PM top, Dev bottom)
echo "Setting up Window 2: Frontend Team..."
tmux new-window -t "$SESSION_NAME:2" -n "Frontend" -c "$PROJECT_DIR"
tmux send-keys -t "$SESSION_NAME:2" "cd '$PROJECT_DIR'" Enter
tmux send-keys -t "$SESSION_NAME:2" "echo '=== Frontend PM ===' && echo 'Starting Claude...'" Enter
tmux send-keys -t "$SESSION_NAME:2" "claude --dangerously-skip-permissions" Enter

# Split for frontend developer (50% height)
sleep 2
tmux split-window -t "$SESSION_NAME:2" -v -p 50 -c "$PROJECT_DIR"
tmux send-keys -t "$SESSION_NAME:2.1" "cd '$PROJECT_DIR'" Enter
tmux send-keys -t "$SESSION_NAME:2.1" "echo '=== Frontend Developer ===' && echo 'Starting Claude...'" Enter
tmux send-keys -t "$SESSION_NAME:2.1" "claude --dangerously-skip-permissions" Enter

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Window Layout:"
echo "  0: Dashboard (top) + Orchestrator (bottom)"
echo "  1: Backend PM (top) + Backend Dev (bottom)"
echo "  2: Frontend PM (top) + Frontend Dev (bottom)"
echo ""
echo "Switch windows: Ctrl+s then window number"
echo "Switch panes: Ctrl+s then arrow keys"
echo ""
echo "Waiting for Claude agents to start (10 seconds)..."
sleep 10

echo ""
echo "Ready to send briefings to agents!"
echo "Run: $SCRIPT_DIR/send_briefings.sh $SESSION_NAME"
