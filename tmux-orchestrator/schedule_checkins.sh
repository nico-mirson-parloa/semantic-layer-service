#!/bin/bash
# Schedule orchestrator check-ins

SESSION_NAME="${1:-semantic-layer}"
ORCHESTRATOR_PANE="${2:-$SESSION_NAME:0.1}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "=== Scheduling Orchestrator Check-ins ==="
echo ""

# Function to schedule check-in
schedule_checkin() {
    local minutes=$1
    local message=$2

    echo "⏰ Scheduling check-in #$((minutes/15)) in $minutes minutes..."

    # Calculate sleep time
    sleep_time=$((minutes * 60))

    # Schedule in background
    (
        sleep $sleep_time
        "$SCRIPT_DIR/send-claude-message.sh" "$ORCHESTRATOR_PANE" "$message"
    ) &

    local pid=$!
    echo "  └─ Scheduled (PID: $pid) to run at $(date -v +${minutes}M '+%H:%M:%S' 2>/dev/null || date -d "+${minutes} minutes" '+%H:%M:%S' 2>/dev/null)"
}

# Schedule check-ins every 15 minutes
schedule_checkin 15 "CHECK-IN #1: Review progress of all 4 agents. Check dashboard for activity. Use send-claude-message.sh to ask status updates if needed. Targets: $SESSION_NAME:1.0 (Backend PM), $SESSION_NAME:1.1 (Backend Dev), $SESSION_NAME:2.0 (Frontend PM), $SESSION_NAME:2.1 (Frontend Dev)"

schedule_checkin 30 "CHECK-IN #2: Review progress since last check. Ensure backend and frontend teams are coordinating on API contracts. Check for blockers. Verify commits are being made."

schedule_checkin 45 "CHECK-IN #3: Mid-session progress review. Check if backend has core APIs ready. Check if frontend has basic routing and API layer. Address any coordination issues."

schedule_checkin 60 "CHECK-IN #4: One hour mark. Review all commits made. Verify backend and frontend are integrating properly. Check implementation quality against specs. Run: git log --oneline -10"

schedule_checkin 75 "CHECK-IN #5: Progress update. Check if teams need guidance or have blockers. Review dashboard activity."

schedule_checkin 90 "CHECK-IN #6: 90-minute mark. Final progress review. Assess what's been completed. Create summary of work done."

echo ""
echo "✅ Check-ins scheduled!"
echo "   Check-ins will happen at: 15min, 30min, 45min, 60min, 75min, 90min"
echo ""
echo "📊 View dashboard anytime in Window 0"
