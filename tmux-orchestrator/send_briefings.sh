#!/bin/bash
# Send briefings to all agents

SESSION_NAME="${1:-semantic-layer}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "=== Sending Briefings to All Agents ==="
echo ""

# Backend PM Briefing
echo "📤 Sending briefing to Backend PM..."
"$SCRIPT_DIR/send-claude-message.sh" "$SESSION_NAME:2.0" "You are the Backend Project Manager for the semantic-layer-service. Your responsibilities:

1. Review specifications/03-BACKEND-SPECIFICATION.md
2. Break down backend implementation into phases
3. Create detailed plan for Backend Developer (in pane below you)
4. Focus on: FastAPI setup, Databricks integration, semantic model CRUD, query execution, AI model generation
5. Use spec-driven-pm approach - establish requirements before work begins
6. Coordinate with Frontend PM on API contracts
7. Commit progress every 30 minutes

Start by reading the specifications and creating your implementation plan."

sleep 3

# Backend Developer Briefing
echo "📤 Sending briefing to Backend Developer..."
"$SCRIPT_DIR/send-claude-message.sh" "$SESSION_NAME:2.1" "You are the Backend Developer for the semantic-layer-service. Your responsibilities:

1. Wait for plan from Backend PM (in pane above you)
2. Implement backend according to specifications/03-BACKEND-SPECIFICATION.md
3. Follow project guidelines in .claude/CLAUDE.md
4. Start with: project structure, FastAPI app, Databricks connector, semantic model services
5. Commit progress every 30 minutes using conventional commit format
6. Coordinate with Backend PM on progress

Wait for PM's plan, then begin implementation."

sleep 3

# Frontend PM Briefing
echo "📤 Sending briefing to Frontend PM..."
"$SCRIPT_DIR/send-claude-message.sh" "$SESSION_NAME:3.0" "You are the Frontend Project Manager for the semantic-layer-service. Your responsibilities:

1. Review specifications/04-FRONTEND-SPECIFICATION.md
2. Break down frontend implementation into phases
3. Create detailed plan for Frontend Developer (in pane below you)
4. Focus on: React app structure, routing, API integration, key pages (MetricsExplorer, QueryLab, ModelsPage)
5. Coordinate with Backend PM on API contracts
6. Commit progress every 30 minutes

Start by reading the specifications and creating your implementation plan."

sleep 3

# Frontend Developer Briefing
echo "📤 Sending briefing to Frontend Developer..."
"$SCRIPT_DIR/send-claude-message.sh" "$SESSION_NAME:3.1" "You are the Frontend Developer for the semantic-layer-service. Your responsibilities:

1. Wait for plan from Frontend PM (in pane above you)
2. Implement frontend according to specifications/04-FRONTEND-SPECIFICATION.md
3. Use: React 18, TypeScript, React Router, React Query, Tailwind CSS, Material-UI
4. Start with: project structure, routing, API layer, then key pages
5. Commit progress every 30 minutes using conventional commit format
6. Coordinate with Frontend PM on progress

Wait for PM's plan, then begin implementation."

sleep 2

echo ""
echo "✅ All briefings sent!"
echo ""
echo "📊 Monitor progress in Dashboard (Window 1)"
echo "🔄 Switch to teams: Window 2 (Backend), Window 3 (Frontend)"
