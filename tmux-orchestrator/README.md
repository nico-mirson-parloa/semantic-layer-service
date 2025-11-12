# Tmux Orchestrator

Coordinate multiple Claude agents across tmux sessions for autonomous development.

## Installation

```bash
# From any project directory
~/path/to/Tmux-Orchestrator/setup_tmux_orchestrator.sh --all
```

This installs:
- Global CLI tools in `~/.local/bin` (tmux-send-claude, tmux-schedule, tmux-orchestrate)
- Claude slash commands in `.claude/commands/` (/orchestrator, /deploy-agent, /agent-status, /coordinate, /schedule-check)

## Usage

### From Terminal (Global Commands)

```bash
# Send message to any Claude agent
tmux-send-claude session:window "Your message"

# Schedule check-ins
tmux-schedule 30 "Check progress note" "session:window"

# Get status of all sessions
tmux-orchestrate
```

### From Claude (Slash Commands)

```
/orchestrator       - Become the orchestrator
/deploy-agent       - Deploy PM/engineer/QA agents
/agent-status       - Check all agent status
/coordinate         - Coordinate between agents
/schedule-check     - Schedule next check-in
```

## Setup Options

```bash
# Install everything (recommended)
./setup_tmux_orchestrator.sh --all

# Install global commands only
./setup_tmux_orchestrator.sh --global

# Install project commands only
./setup_tmux_orchestrator.sh --project-commands

# Custom orchestrator path
./setup_tmux_orchestrator.sh --all --orchestrator-path /custom/path

# Show help
./setup_tmux_orchestrator.sh --help
```

## Architecture

```
Orchestrator (You)
    ├── Project Manager
    │   ├── Engineer 1
    │   ├── Engineer 2
    │   └── QA
    └── Project Manager 2
        └── Engineers...
```

## Core Files

- `setup_tmux_orchestrator.sh` - Installation script
- `send-claude-message.sh` - Send messages to agents
- `schedule_with_note.sh` - Schedule agent check-ins
- `tmux_utils.py` - Tmux utilities
- `CLAUDE.md` - Agent behavior instructions

## Quick Example

```bash
# 1. Install in your project
cd ~/my-project
~/Tmux-Orchestrator/setup_tmux_orchestrator.sh --all

# 2. Start tmux and Claude
tmux new-session -s myapp
claude

# 3. Become orchestrator
/orchestrator

# 4. Deploy agents
"Create a PM to implement user authentication"

# 5. Agents work autonomously
# - PM deploys engineers
# - Engineers implement features
# - Everyone commits every 30 minutes
# - Progress reported back
```

## Using as a Subfolder in Another Repo

To include this in another repository:

```bash
# Copy essential files
cp -r Tmux-Orchestrator/setup_tmux_orchestrator.sh your-repo/orchestrator/
cp -r Tmux-Orchestrator/send-claude-message.sh your-repo/orchestrator/
cp -r Tmux-Orchestrator/schedule_with_note.sh your-repo/orchestrator/
cp -r Tmux-Orchestrator/tmux_utils.py your-repo/orchestrator/
cp -r Tmux-Orchestrator/CLAUDE.md your-repo/orchestrator/
cp -r Tmux-Orchestrator/.claude your-repo/orchestrator/

# Then run setup
cd your-repo
./orchestrator/setup_tmux_orchestrator.sh --all
```

Or better yet, use as a git submodule:

```bash
cd your-repo
git submodule add <tmux-orchestrator-url> orchestrator
./orchestrator/setup_tmux_orchestrator.sh --all
```

## License

MIT
