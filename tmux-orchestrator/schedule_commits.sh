#!/bin/bash
# Schedule auto-commits for all agents

SESSION_NAME="${1:-semantic-layer}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "=== Scheduling Auto-Commits ==="
echo ""

# Function to schedule commit
schedule_commit() {
    local target=$1
    local name=$2
    local minutes=$3

    echo "⏰ Scheduling commit for $name in $minutes minutes..."

    # Calculate sleep time
    sleep_time=$((minutes * 60))

    # Schedule in background
    (
        sleep $sleep_time
        "$SCRIPT_DIR/send-claude-message.sh" "$target" "TIME TO COMMIT: Create a git commit with all your current progress. Use conventional commit format from .claude/CLAUDE.md. Include a summary of what you've accomplished since the last commit."
    ) &

    local pid=$!
    echo "  └─ Scheduled (PID: $pid) to run at $(date -v +${minutes}M '+%H:%M:%S' 2>/dev/null || date -d "+${minutes} minutes" '+%H:%M:%S' 2>/dev/null)"
}

# Schedule commits every 30 minutes for all developers
schedule_commit "$SESSION_NAME:1.1" "Backend Developer" 30
schedule_commit "$SESSION_NAME:2.1" "Frontend Developer" 30

# Schedule second round of commits
schedule_commit "$SESSION_NAME:1.1" "Backend Developer" 60
schedule_commit "$SESSION_NAME:2.1" "Frontend Developer" 60

# Schedule third round
schedule_commit "$SESSION_NAME:1.1" "Backend Developer" 90
schedule_commit "$SESSION_NAME:2.1" "Frontend Developer" 90

echo ""
echo "✅ Auto-commits scheduled!"
echo "   Commits will happen at: 30min, 60min, 90min"
