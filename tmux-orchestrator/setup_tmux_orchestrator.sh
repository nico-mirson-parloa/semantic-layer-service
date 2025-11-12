#!/bin/bash
# setup_tmux_orchestrator.sh - Install Tmux Orchestrator tools in any repository
#
# This script sets up the Tmux Orchestrator system in any project, allowing you to:
# - Use tmux-orchestrator tools from any directory
# - Create Claude slash commands that leverage the orchestrator
# - Access orchestrator utilities without copying files
#
# Usage:
#   ./setup_tmux_orchestrator.sh [OPTIONS]
#
# Options:
#   --global              Install globally in ~/.local/bin
#   --project-commands    Create .claude/commands for this project
#   --all                 Do both global and project setup
#   --orchestrator-path   Override orchestrator path (default: auto-detect)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ORCHESTRATOR_PATH=""
INSTALL_GLOBAL=false
INSTALL_PROJECT_COMMANDS=false

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to detect orchestrator path
detect_orchestrator_path() {
    local script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

    # If running from orchestrator directory
    if [[ -f "$script_dir/send-claude-message.sh" ]] && [[ -f "$script_dir/tmux_utils.py" ]]; then
        echo "$script_dir"
        return 0
    fi

    # Check common locations
    local common_paths=(
        "$HOME/Repos/Tmux-Orchestrator"
        "$HOME/Coding/Tmux-Orchestrator"
        "$HOME/Projects/Tmux-Orchestrator"
        "$HOME/tmux-orchestrator"
    )

    for path in "${common_paths[@]}"; do
        if [[ -f "$path/send-claude-message.sh" ]] && [[ -f "$path/tmux_utils.py" ]]; then
            echo "$path"
            return 0
        fi
    done

    return 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --global)
            INSTALL_GLOBAL=true
            shift
            ;;
        --project-commands)
            INSTALL_PROJECT_COMMANDS=true
            shift
            ;;
        --all)
            INSTALL_GLOBAL=true
            INSTALL_PROJECT_COMMANDS=true
            shift
            ;;
        --orchestrator-path)
            ORCHESTRATOR_PATH="$2"
            shift 2
            ;;
        -h|--help)
            cat << EOF
Tmux Orchestrator Setup Script

Usage: $0 [OPTIONS]

Options:
  --global              Install orchestrator tools globally in ~/.local/bin
  --project-commands    Create .claude/commands in current project
  --all                 Perform both global and project setup
  --orchestrator-path   Specify orchestrator directory path
  -h, --help            Show this help message

Examples:
  # Install globally
  $0 --global

  # Set up commands in current project
  $0 --project-commands

  # Do everything
  $0 --all

  # Use custom orchestrator path
  $0 --all --orchestrator-path /path/to/orchestrator
EOF
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# If no options specified, show help
if [[ "$INSTALL_GLOBAL" == false ]] && [[ "$INSTALL_PROJECT_COMMANDS" == false ]]; then
    print_warning "No installation options specified. Use --help for options."
    print_info "Quick start: $0 --all"
    exit 1
fi

# Detect or validate orchestrator path
if [[ -z "$ORCHESTRATOR_PATH" ]]; then
    print_info "Detecting Tmux Orchestrator path..."
    ORCHESTRATOR_PATH=$(detect_orchestrator_path)
    if [[ $? -ne 0 ]]; then
        print_error "Could not detect Tmux Orchestrator path."
        print_info "Please specify path with --orchestrator-path"
        exit 1
    fi
fi

# Validate orchestrator path
if [[ ! -d "$ORCHESTRATOR_PATH" ]]; then
    print_error "Orchestrator path does not exist: $ORCHESTRATOR_PATH"
    exit 1
fi

if [[ ! -f "$ORCHESTRATOR_PATH/send-claude-message.sh" ]] || [[ ! -f "$ORCHESTRATOR_PATH/tmux_utils.py" ]]; then
    print_error "Path does not contain required orchestrator files: $ORCHESTRATOR_PATH"
    exit 1
fi

print_success "Found Tmux Orchestrator at: $ORCHESTRATOR_PATH"

# Global installation
if [[ "$INSTALL_GLOBAL" == true ]]; then
    print_info "Installing orchestrator tools globally..."

    # Create ~/.local/bin if it doesn't exist
    mkdir -p "$HOME/.local/bin"

    # Create wrapper scripts that point to orchestrator
    cat > "$HOME/.local/bin/tmux-send-claude" << EOF
#!/bin/bash
# Wrapper for send-claude-message.sh
exec "$ORCHESTRATOR_PATH/send-claude-message.sh" "\$@"
EOF
    chmod +x "$HOME/.local/bin/tmux-send-claude"

    cat > "$HOME/.local/bin/tmux-schedule" << EOF
#!/bin/bash
# Wrapper for schedule_with_note.sh
exec "$ORCHESTRATOR_PATH/schedule_with_note.sh" "\$@"
EOF
    chmod +x "$HOME/.local/bin/tmux-schedule"

    cat > "$HOME/.local/bin/tmux-orchestrate" << EOF
#!/usr/bin/env python3
# Wrapper for tmux_utils.py
import sys
import subprocess
sys.exit(subprocess.call(['python3', '$ORCHESTRATOR_PATH/tmux_utils.py'] + sys.argv[1:]))
EOF
    chmod +x "$HOME/.local/bin/tmux-orchestrate"

    print_success "Installed global tools:"
    print_success "  - tmux-send-claude (send messages to Claude agents)"
    print_success "  - tmux-schedule (schedule agent check-ins)"
    print_success "  - tmux-orchestrate (get tmux status)"

    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        print_warning "~/.local/bin is not in your PATH"
        print_info "Add this to your ~/.bashrc or ~/.zshrc:"
        echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
fi

# Project commands installation
if [[ "$INSTALL_PROJECT_COMMANDS" == true ]]; then
    print_info "Creating .claude/commands in current directory..."

    # Get current directory
    CURRENT_DIR="$(pwd)"

    # Create .claude/commands directory
    mkdir -p "$CURRENT_DIR/.claude/commands"

    # Create orchestrator command
    cat > "$CURRENT_DIR/.claude/commands/orchestrator.md" << 'EOF'
---
description: Create and manage tmux orchestrator for multi-agent coordination
---

You are now acting as the Tmux Orchestrator. Your role is to:

1. **Coordinate Multiple Agents**: Deploy and manage project managers and engineers
2. **Monitor Progress**: Check on agent status across tmux sessions
3. **Resolve Issues**: Help agents when they're blocked
4. **Maintain Quality**: Ensure code quality and git discipline

## Available Tools

You have access to orchestrator utilities:
- `tmux-send-claude <session:window> "message"` - Send messages to agents
- `tmux-schedule <minutes> "note" [window]` - Schedule check-ins
- `tmux-orchestrate` - Get status of all tmux sessions

## Key Responsibilities

1. **Agent Deployment**: Create project managers with clear specifications
2. **Hub-and-Spoke Communication**: Agents report to PMs, PMs report to you
3. **Self-Scheduling**: Schedule your own check-ins to maintain oversight
4. **Git Discipline**: Ensure all agents commit every 30 minutes

## Getting Started

First, analyze the current tmux environment:
```bash
tmux-orchestrate
```

Then decide if you need to:
- Create new project managers for projects
- Check in on existing agents
- Coordinate cross-project work

Remember: You're the high-level coordinator. Don't get bogged down in implementation details.
EOF

    # Create deploy-agent command
    cat > "$CURRENT_DIR/.claude/commands/deploy-agent.md" << 'EOF'
---
description: Deploy a new Claude agent (PM or engineer) in a tmux window
---

Deploy a new agent to work on this project.

Parse the arguments to determine:
1. **Agent Type**: project-manager, engineer, qa, devops, reviewer
2. **Session Name**: Which tmux session to use
3. **Specification**: What the agent should work on

## Deployment Steps

1. **Create Tmux Window**
   ```bash
   tmux new-window -t <session> -n "<Agent-Type>" -c "$(pwd)"
   ```

2. **Start Claude**
   ```bash
   tmux send-keys -t <session>:<window> "claude --dangerously-skip-permissions" Enter
   sleep 5
   ```

3. **Brief the Agent**
   ```bash
   tmux-send-claude <session>:<window> "<Role-specific briefing>"
   ```

## Agent Briefing Templates

### Project Manager
"You are the Project Manager for [project]. Your responsibilities:
1. Maintain high quality standards
2. Coordinate with engineers
3. Schedule regular check-ins
4. Report progress to orchestrator

First, read the specification and create a plan."

### Engineer
"You are a software engineer working on [project]. Your responsibilities:
1. Implement features from the spec
2. Commit every 30 minutes
3. Report to the project manager
4. Ask questions when blocked

First, analyze the codebase and current status."

### QA Engineer
"You are the QA engineer for [project]. Your responsibilities:
1. Test all new features
2. Verify specifications are met
3. Report bugs to engineers
4. Maintain test coverage

First, review the test suite and recent changes."

## After Deployment

Monitor the agent's initial response and ensure they:
- Understand their role
- Have access to necessary files
- Can start working independently

Use `tmux capture-pane -t <session>:<window> -p | tail -50` to check progress.

# Usage Examples:
# /deploy-agent project-manager in session ai-chat for user authentication feature
# /deploy-agent engineer in session backend to optimize database queries
EOF

    # Create agent-status command
    cat > "$CURRENT_DIR/.claude/commands/agent-status.md" << 'EOF'
---
description: Get status of all Claude agents across tmux sessions
---

Check the status of all running Claude agents.

## Steps

1. **Get All Sessions**
   ```bash
   tmux-orchestrate
   ```

2. **Analyze Output**
   Look for:
   - Active Claude instances
   - Recent output from agents
   - Signs of errors or blocking issues
   - Work completion indicators

3. **Report Summary**
   Provide a concise summary:
   - Which agents are active
   - What each is working on
   - Any blockers or issues
   - Recommended next actions

## Example Analysis

```
Session: frontend
  Window 0: Project-Manager (ACTIVE)
    Recent: "Waiting for engineer to complete login form"
  Window 1: Engineer
    Recent: "Running npm run dev... Server started on port 3000"
    Status: Working on feature implementation

Session: backend
  Window 0: Engineer
    Recent: "ERROR: Port 8000 already in use"
    Status: BLOCKED - needs intervention
```

## Action Items

After status check, identify:
- Agents needing help
- Work ready for review
- Completed tasks requiring acknowledgment
- Schedule next check-in

Use `tmux-schedule <minutes> "Next status check"` to schedule your next check-in.
EOF

    # Create coordinate command
    cat > "$CURRENT_DIR/.claude/commands/coordinate.md" << 'EOF'
---
description: Coordinate work between multiple agents and projects
---

Facilitate coordination between agents working on related tasks.

Parse the arguments to identify:
1. **Source Agent**: Who has information/needs
2. **Target Agent**: Who needs information/can help
3. **Coordination Type**: Information sharing, dependency resolution, or cross-project sync

## Coordination Patterns

### Information Sharing
When one agent has information another needs:
```bash
# Get info from source
tmux capture-pane -t <source-session>:<window> -p | tail -50

# Share with target
tmux-send-claude <target-session>:<window> "Update from [source]: [key information]"
```

### Dependency Resolution
When agents are blocked on each other:
```bash
# Check blocker status
tmux capture-pane -t <blocking-session>:<window> -p | tail -50

# Update blocked agent
tmux-send-claude <blocked-session>:<window> "Dependency update: [status and timeline]"
```

### Cross-Project Synchronization
When projects need to align:
```bash
# Get status from both projects
tmux-orchestrate

# Send alignment message
tmux-send-claude <project1>:0 "Project 2 is using [approach], please align"
tmux-send-claude <project2>:0 "Project 1 is using [approach], please align"
```

## Communication Best Practices

1. **Be Specific**: Include exact details, not vague updates
2. **Include Context**: Agents don't see other conversations
3. **Set Expectations**: Provide timelines or next steps
4. **Follow Up**: Schedule check-in to verify coordination succeeded

## Example Scenarios

### Frontend needs API endpoint from Backend
```bash
# Check what frontend needs
tmux capture-pane -t frontend:1 -p | grep -i "api\|endpoint"

# Ask backend
tmux-send-claude backend:0 "Frontend needs: POST /api/auth/login endpoint with email/password. What's the status?"

# Wait for response, then relay back
tmux-send-claude frontend:1 "Backend confirms: POST /api/auth/login is ready. Returns JWT token in response.token"
```

# Usage Examples:
# /coordinate frontend engineer with backend about API endpoints
# /coordinate project-manager-1 with project-manager-2 about shared database schema
EOF

    # Create schedule-check command
    cat > "$CURRENT_DIR/.claude/commands/schedule-check.md" << 'EOF'
---
description: Schedule your next orchestrator check-in
---

Schedule when you should check back on agent progress.

Parse the arguments to determine:
1. **Time**: Minutes until next check (default: 30)
2. **Focus**: What to check on next time
3. **Target**: Which window you're running in (critical!)

## Scheduling Protocol

1. **Identify Current Window**
   ```bash
   CURRENT_WINDOW=$(tmux display-message -p "#{session_name}:#{window_index}")
   echo "I am running in: $CURRENT_WINDOW"
   ```

2. **Create Specific Note**
   Write a clear, actionable note:
   - ✓ "Check if engineer completed auth feature, review code"
   - ✓ "Verify tests are passing, coordinate next feature"
   - ✗ "Check on things" (too vague)
   - ✗ "Follow up" (no specifics)

3. **Schedule the Check**
   ```bash
   tmux-schedule <minutes> "<specific note>" "$CURRENT_WINDOW"
   ```

## Timing Guidelines

- **15 minutes**: Active development, frequent issues
- **30 minutes**: Standard progress monitoring
- **60 minutes**: Stable work, experienced agents
- **120 minutes**: Overnight or background tasks

## Example Schedules

### Active Development
```bash
tmux-schedule 15 "Check auth implementation progress, verify commits" "$CURRENT_WINDOW"
```

### Cross-Project Coordination
```bash
tmux-schedule 30 "Verify frontend and backend API alignment, test integration" "$CURRENT_WINDOW"
```

### Quality Check
```bash
tmux-schedule 45 "Review test coverage, check for security issues, verify git commits" "$CURRENT_WINDOW"
```

## Important Notes

- **Always** specify the target window (your current window)
- **Never** schedule to a different window unless intentional
- **Test** the schedule before relying on it

# Usage Examples:
# /schedule-check in 30 minutes to verify authentication feature completion
# /schedule-check in 60 minutes for cross-project API synchronization check
EOF

    print_success "Created Claude commands in .claude/commands/:"
    print_success "  - /orchestrator - Act as tmux orchestrator"
    print_success "  - /deploy-agent - Deploy new agent (PM/engineer/QA)"
    print_success "  - /agent-status - Check all agent status"
    print_success "  - /coordinate - Coordinate between agents"
    print_success "  - /schedule-check - Schedule next check-in"

    # Create a .env file with orchestrator path if it doesn't exist
    if [[ ! -f "$CURRENT_DIR/.env.orchestrator" ]]; then
        cat > "$CURRENT_DIR/.env.orchestrator" << EOF
# Tmux Orchestrator Configuration
ORCHESTRATOR_PATH="$ORCHESTRATOR_PATH"
ORCHESTRATOR_SEND_MESSAGE="$ORCHESTRATOR_PATH/send-claude-message.sh"
ORCHESTRATOR_SCHEDULE="$ORCHESTRATOR_PATH/schedule_with_note.sh"
ORCHESTRATOR_UTILS="$ORCHESTRATOR_PATH/tmux_utils.py"
EOF
        print_success "Created .env.orchestrator with paths"
    fi
fi

# Print summary
echo ""
print_success "Setup complete!"
echo ""
print_info "Orchestrator path: $ORCHESTRATOR_PATH"

if [[ "$INSTALL_GLOBAL" == true ]]; then
    echo ""
    print_info "Global commands available:"
    echo "  tmux-send-claude <session:window> \"message\""
    echo "  tmux-schedule <minutes> \"note\" [window]"
    echo "  tmux-orchestrate"
fi

if [[ "$INSTALL_PROJECT_COMMANDS" == true ]]; then
    echo ""
    print_info "Claude commands available in this project:"
    echo "  /orchestrator - Become the orchestrator"
    echo "  /deploy-agent - Deploy agents to tmux"
    echo "  /agent-status - Check agent status"
    echo "  /coordinate - Coordinate between agents"
    echo "  /schedule-check - Schedule check-ins"
fi

echo ""
print_info "Documentation: $ORCHESTRATOR_PATH/README.md"
print_info "Examples: $ORCHESTRATOR_PATH/Examples/"
