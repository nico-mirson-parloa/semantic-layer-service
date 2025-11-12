# Semantic Layer Service

A modern semantic layer service that generates semantic models from Databricks gold layer transformations, providing a unified interface for metrics, dimensions, and business intelligence.

> **🤖 Built with Claude Code**: This entire project was developed using [Claude Code](https://claude.com/claude-code) following a specification-driven PM workflow with multi-agent orchestration. See the [Development Process](#development-process) section for details.

## Architecture Overview

### Core Components
- **Backend API**: FastAPI-based service with Databricks integration
- **Frontend Application**: React-based UI for metrics management and querying
- **Semantic Engine**: YAML-based model definitions with query optimization
- **Databricks Integration**: Unity Catalog metadata discovery and SQL execution
- **SQL API**: PostgreSQL-compatible interface for BI tools and SQL clients

### Key Features

#### Core Capabilities
- Interactive metrics and dimensions builder
- Real-time query execution and caching
- Git-based version control for semantic models
- Unity Catalog integration for metadata discovery
- Row-level security and access control
- **PostgreSQL-compatible SQL API** for universal BI tool connectivity

#### Advanced Features
- **Automatic Model Generation**: AI-powered generation from gold layer tables
  - Intelligent pattern recognition and analysis
  - Industry-specific metric suggestions with confidence scoring
  - Interactive customization wizard
  - One-click YAML generation and validation
- **Documentation Generation**: Auto-generate comprehensive documentation
  - Multiple export formats (Markdown, HTML, PDF, Confluence)
  - Template system for different audiences
  - Usage examples and best practices
- **Lineage Visualization**: Interactive data lineage tracking
  - Table and column-level lineage graphs
  - Impact analysis and dependency tracking
  - Real-time updates from Unity Catalog

## Project Structure

```
semantic-layer-service/
├── backend/                 # FastAPI backend service
│   ├── app/
│   │   ├── api/            # REST API endpoints
│   │   ├── core/           # Core business logic
│   │   ├── integrations/   # Databricks, external integrations
│   │   ├── models/         # Data models and schemas
│   │   └── services/       # Business services
│   └── requirements.txt
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Main application pages
│   │   ├── services/       # API client services
│   │   └── utils/          # Utility functions
│   └── package.json
├── semantic-models/        # YAML semantic model definitions
├── specifications/         # Technical specifications and documentation
├── tmux-orchestrator/      # Multi-agent orchestration scripts
├── examples/               # Usage examples and demos
└── docker-compose.yml      # Local development setup
```

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Pydantic**: Data validation
- **Databricks SQL Connector**: Direct connection to SQL Warehouse
- **PyYAML**: Semantic model parsing
- **Structlog**: Structured logging

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **React Query**: State management and caching
- **Recharts**: Data visualization

### Infrastructure
- **Docker**: Containerization
- **Databricks**: All data storage and processing
- **Git**: Version control for semantic models

## Getting Started

### Prerequisites
- Python 3.11+ and Node.js 18+
- Docker and Docker Compose (optional)
- Databricks workspace access with Unity Catalog enabled

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/nico-mirson-parloa/semantic-layer-service.git
   cd semantic-layer-service
   ```

2. **Configure environment variables**
   ```bash
   cp env.example .env
   ```

   Edit `.env` with your Databricks credentials:
   ```env
   DATABRICKS_HOST=your-workspace.cloud.databricks.com
   DATABRICKS_TOKEN=your-personal-access-token
   DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
   DATABRICKS_GENIE_SPACE_ID=your-genie-space-id  # Optional
   DEBUG=false
   ```

3. **Quick Setup with Virtual Environment**
   ```bash
   # Create and activate virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install backend dependencies
   pip install -r backend/requirements.txt

   # Install frontend dependencies
   cd frontend && npm install && cd ..
   ```

4. **Start the services**

   **Option A: Using convenience scripts**
   ```bash
   # Start backend (in one terminal)
   ./start_backend.sh

   # Start frontend (in another terminal)
   ./start_frontend.sh
   ```

   **Option B: Using Docker**
   ```bash
   docker-compose up -d
   ```

5. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - SQL API: localhost:5433 (PostgreSQL protocol)

6. **Start SQL API Server** (Optional - for BI tool connectivity)
   ```bash
   cd backend
   python start_sql_server.py
   ```

## 🤖 Tmux Orchestrator

This project includes an innovative AI-powered development workflow using tmux sessions and multiple Claude Code agents orchestrated together.

> **Note**: This setup uses a custom tmux configuration with `Ctrl+s` as the prefix key. See the [Tmux Commands Reference](#tmux-commands-reference) section for all available keybindings.

### What is the Tmux Orchestrator?

The tmux orchestrator is a system where multiple Claude Code agents work simultaneously across different tmux windows/panes, each responsible for different aspects of the codebase:

- **Orchestrator**: High-level oversight and coordination
- **Project Manager**: Quality standards and team coordination
- **Developers**: Implementation and technical decisions
- **QA Engineers**: Testing and verification
- **Code Reviewers**: Security and best practices

### Directory Structure

```
tmux-orchestrator/
├── CLAUDE.md                      # Orchestrator knowledge base and protocols
├── setup_tmux_orchestrator.sh     # Main setup script
├── send-claude-message.sh         # Inter-agent communication script
├── schedule_with_note.sh          # Task scheduling script
└── registry/                      # Agent logs and session tracking
```

### Key Scripts

#### `setup_tmux_orchestrator.sh`
Sets up the entire tmux session structure with multiple Claude agents:
```bash
./tmux-orchestrator/setup_tmux_orchestrator.sh
```

Creates:
- **Orchestrator window**: Central coordination
- **Project Manager window**: Quality oversight
- **Developer windows**: Backend and frontend agents
- **Shell windows**: For running services

#### `send-claude-message.sh`
Sends messages between agents with proper timing:
```bash
./tmux-orchestrator/send-claude-message.sh <target-window> "Your message here"

# Example:
./tmux-orchestrator/send-claude-message.sh semantic:1 "What's the status of the API endpoint implementation?"
```

#### `schedule_with_note.sh`
Schedules follow-up checks and reminders:
```bash
./schedule_with_note.sh <minutes> "<note>" <target-window>

# Example:
./schedule_with_note.sh 30 "Check backend deployment status" semantic:0
```

### Quick Setup Guide

#### Step 1: Make Scripts Executable

```bash
cd tmux-orchestrator
chmod +x setup_tmux_orchestrator.sh
chmod +x send-claude-message.sh
chmod +x schedule_with_note.sh
```

#### Step 2: Create Orchestrator Session

```bash
# Create a new tmux session for the orchestrator
tmux new-session -s semantic-layer

# Start Claude Code with permissions bypass
claude --dangerously-skip-permissions
```

#### Step 3: Initialize the Orchestrator

Give Claude this initial prompt:

```
You are an AI orchestrator for the semantic-layer-service project.

First, let's verify the setup:

1. Check what tmux window you're in:
   Run: tmux display-message -p "#{session_name}:#{window_index}"

2. Test the scheduling script:
   Run: ./tmux-orchestrator/schedule_with_note.sh 1 "Test message" semantic-layer:0

3. If both work, tell me "Setup successful!"

Then I'll give you the project specifications to work on.
```

#### Step 4: Start the Development Workflow

Once setup is verified, give Claude this prompt:

```
I need you to work on the semantic-layer-service project following the specifications in ./specifications/

Please:
1. Read the specifications in ./specifications/ (start with 00-INDEX.md)
2. Create a backend team (PM + Developer) in separate tmux windows
3. Create a frontend team (PM + Developer) in separate tmux windows
4. Have them build according to the specs
5. Check on both teams every 15 minutes
6. Ensure 30-minute auto-commits for all agents

Key files to reference:
- .claude/CLAUDE.md - Project-specific development guidelines
- specifications/00-INDEX.md - Overview of all specifications
- specifications/03-BACKEND-SPECIFICATION.md - Backend implementation details
- specifications/04-FRONTEND-SPECIFICATION.md - Frontend implementation details

Start both teams working simultaneously. Coordinate work between backend and frontend.
```

#### Step 5: Monitor the Agents

```bash
# See all tmux sessions
tmux ls

# See what a specific agent is doing (replace window number)
tmux capture-pane -t semantic-layer:0 -p | tail -30   # Orchestrator
tmux capture-pane -t semantic-layer:1 -p | tail -30   # PM
tmux capture-pane -t semantic-layer:2 -p | tail -30   # Backend Developer
tmux capture-pane -t semantic-layer:3 -p | tail -30   # Frontend Developer

# Send a message to an agent
./tmux-orchestrator/send-claude-message.sh semantic-layer:2 "What's your current status?"
```

### Using the Orchestrator

1. **Attach to the session**:
   ```bash
   tmux attach-session -t semantic-layer
   ```

2. **Navigate between windows**:
   - `Ctrl+s 0-9`: Switch to window 0-9
   - `Ctrl+s n`: Create new session
   - `Ctrl+s [`: Previous window
   - `Ctrl+s ]`: Next window
   - Mouse click: Click on window in status bar (mouse support enabled)

3. **Communicate with agents**:
   ```bash
   # From orchestrator window, send messages to other agents
   ./tmux-orchestrator/send-claude-message.sh semantic-layer:2 "Please implement the authentication endpoint"
   ```

4. **Monitor agent work**:
   ```bash
   # Capture output from an agent's window
   tmux capture-pane -t semantic-layer:2 -p | tail -50
   ```

### Example Workflow

Here's a complete example of starting a new feature:

```bash
# 1. Start tmux session
tmux new-session -s semantic-layer

# 2. Start Claude orchestrator
claude --dangerously-skip-permissions

# 3. Give orchestrator the initialization prompt (see Step 3 above)

# 4. Once verified, give the development workflow prompt (see Step 4 above)

# 5. Detach from session to let agents work
Ctrl+s d

# 6. Check back later to see progress
tmux attach-session -t semantic-layer

# 7. Monitor specific agents
tmux capture-pane -t semantic-layer:2 -p | tail -30

# 8. Send messages to guide agents
./tmux-orchestrator/send-claude-message.sh semantic-layer:1 "Update on backend API status?"
```

### Tmux Commands Reference

Your tmux configuration uses `Ctrl+s` as the prefix key (instead of the default `Ctrl+b`).

#### Session Management
- `Ctrl+s n`: Create new session
- `Ctrl+s r`: Rename current session
- `Ctrl+s k`: Kill current session (with confirmation)
- `Ctrl+s d`: Detach from session

#### Window Management
- `Ctrl+s c`: Create new window
- `Ctrl+s d`: Kill current window
- `Ctrl+s 0-9`: Switch to window number 0-9
- `Ctrl+s [`: Previous window
- `Ctrl+s ]`: Next window
- Click window name in status bar with mouse

#### Pane Management
- `Ctrl+s v`: Split window vertically (side by side)
- `Ctrl+s h`: Split window horizontally (top/bottom)
- `Ctrl+s x`: Kill current pane
- `Ctrl+s h/j/k/l`: Navigate between panes (vim-style)
- `Ctrl+Shift+Arrow`: Resize pane in arrow direction
- Mouse: Click to focus pane, drag border to resize

#### Configuration
- `Ctrl+s R`: Reload tmux configuration
- Windows numbered starting from 1 (not 0)
- Mouse support enabled throughout
- Copy mode uses vim keybindings

### Agent Roles and Responsibilities

When the orchestrator creates teams, each agent has specific responsibilities:

#### Orchestrator (Window 0)
- **Role**: High-level coordination and oversight
- **Tasks**:
  - Create and manage agent teams
  - Monitor overall progress
  - Resolve cross-team dependencies
  - Schedule 15-minute check-ins
  - Ensure 30-minute commit discipline
- **Prompts to use**: See Step 3 and Step 4 in Quick Setup

#### Project Manager (Windows 1, 3, etc.)
- **Role**: Team coordination and quality assurance
- **Tasks**:
  - Ensure specs are followed
  - Review code quality
  - Track team progress
  - Report to orchestrator
  - Enforce git discipline
- **Example brief**: "You are the Backend PM. Coordinate with the backend developer, ensure specs in specifications/03-BACKEND-SPECIFICATION.md are followed, and maintain high quality standards."

#### Developer (Windows 2, 4, etc.)
- **Role**: Implementation
- **Tasks**:
  - Write code according to specs
  - Commit every 30 minutes
  - Report to PM
  - Follow .claude/CLAUDE.md guidelines
  - Run tests and linters
- **Example brief**: "You are the Backend Developer. Implement the FastAPI backend according to specifications/03-BACKEND-SPECIFICATION.md. Work with your PM and commit every 30 minutes."

### Benefits

- **Parallel Development**: Multiple agents work simultaneously on different parts
- **24/7 Development**: Agents can work continuously without breaks
- **Quality Assurance**: PM agent ensures high standards are maintained
- **Clear Communication**: Structured messaging protocols prevent confusion
- **Coordinated Workflow**: Orchestrator manages dependencies and priorities
- **Specification-Driven**: All work follows documented specifications
- **Automated Commits**: 30-minute commit discipline prevents work loss

### Best Practices

1. **Always Start with Specs**: Ensure specifications are clear before starting agents
2. **Regular Status Updates**: Agents report progress every 30 minutes
3. **Commit Frequently**: Auto-commit every 30 minutes to prevent work loss
4. **Use Feature Branches**: Each major task gets its own branch
5. **Quality Gates**: PM reviews all work before merging
6. **Clear Communication**: Use structured message templates
7. **Monitor Regularly**: Check agent windows every 15-30 minutes
8. **Use the Scripts**: Always use send-claude-message.sh for inter-agent communication

See [`tmux-orchestrator/CLAUDE.md`](tmux-orchestrator/CLAUDE.md) for complete orchestration protocols and guidelines.

## Development Process

### Specification-Driven Development with Claude Code

This project was built entirely using [Claude Code](https://claude.com/claude-code) with a rigorous PM-led workflow:

1. **Requirements Gathering**: PM agent gathered detailed requirements and created comprehensive specifications
2. **Specification Creation**: Clear problem statements, success criteria, and acceptance criteria documented before any coding
3. **Agent Orchestration**: Multiple specialized agents (databricks-genius, codebase-analyzer, production-code-reviewer) coordinated by PM
4. **Iterative Development**: Spec → Implement → Review → Refine cycle with PM quality gates
5. **Continuous Quality**: All code reviewed against specifications before completion

### Key Principles

- **Never Start Without Specs**: Every feature begins with a documented specification
- **PM-Driven Quality**: PM agent ensures exceptionally high standards throughout
- **Agent Specialization**: Right agent for the right task (databricks-genius for SQL, production-code-reviewer for code quality)
- **Verification Before Completion**: Test everything, trust but verify all work
- **Clear Communication**: Structured status updates and progress tracking

### Custom Claude Code Agents

Located in `.claude/agents/`:
- **spec-driven-pm**: Requirements gathering, specification creation, and work review
- **databricks-genius**: Databricks-specific implementations and best practices
- **codebase-analyzer**: Codebase documentation and pattern analysis
- **web-search-researcher**: Current documentation and technology research
- **production-code-reviewer**: Functional programming and code quality standards
- **test-code-reviewer**: Test code standards and patterns

### Custom Skills (Recipes)

Located in `.claude/skills/`:
- **pm-orchestration-recipe**: Requirements, specifications, and agent coordination patterns
- **databricks-recipe**: Databricks SQL, Python, asset bundles, and DQX framework
- **production-code-recipe**: Functional programming, true-myth patterns, type safety
- **test-code-recipe**: Test architecture, helpers, and Testcontainers usage

See [`.claude/CLAUDE.md`](.claude/CLAUDE.md) for complete project-specific guidance.

## Databricks Integration

### Unity Catalog Connection
- Uses JDBC/ODBC drivers for SQL execution
- Information Schema for metadata discovery
- Unity REST API for external table access
- System tables for lineage tracking

### Supported Features
- Automatic table and column discovery
- Business logic extraction from existing transformations
- Cross-catalog and cross-schema joins
- Real-time query execution against gold layer tables

## SQL API for BI Tools

The service includes a PostgreSQL-compatible SQL interface that allows any SQL client or BI tool to connect and query semantic models:

### Features
- **Universal Connectivity**: Connect Tableau, Power BI, Looker, Excel, or any SQL client
- **Virtual Schemas**: Each semantic model appears as a schema with tables and views
- **Automatic Translation**: SQL queries are automatically translated to semantic queries
- **Standard Protocol**: Uses PostgreSQL wire protocol for maximum compatibility
- **Preset Integration**: Native support for Preset (Apache Superset) with automated setup

### Quick Start
```bash
# Start SQL server
cd backend && python start_sql_server.py

# Connect with psql
psql -h localhost -p 5433 -U user -d semantic_layer

# Query semantic models
SELECT * FROM sem_sales_metrics.fact LIMIT 10;
```

See `backend/app/sql_api/` for implementation details and `examples/sql_api_demo.py` for usage examples.

### Preset (Apache Superset) Integration

The service includes native Preset integration with automated setup:

```bash
# Set up Preset connection and generate configurations
cd backend/app/connectors/preset
python setup_preset.py
```

This will:
- Validate SQL API connectivity
- Generate database connection configs
- Create dataset definitions
- Build dashboard templates
- Export metrics configurations

See `backend/app/connectors/preset/README.md` for complete setup instructions and usage examples.

## Semantic Model Structure

Models are defined in YAML format inspired by dbt Semantic Layer:

```yaml
semantic_model:
  name: sales_metrics
  model: ref('gold_sales_fact')
  entities:
    - name: customer_id
      type: primary
    - name: product_id
      type: foreign
  dimensions:
    - name: order_date
      type: time
      time_granularity: [day, week, month, quarter, year]
    - name: region
      type: categorical
  measures:
    - name: revenue
      agg: sum
      expr: amount
    - name: order_count
      agg: count
      expr: order_id
  metrics:
    - name: total_revenue
      type: simple
      measure: revenue
    - name: avg_order_value
      type: ratio
      numerator: revenue
      denominator: order_count
```

## 📚 Documentation

Project documentation is organized in the following locations:

### Specifications
Detailed technical specifications are in the [`specifications/`](specifications/) directory:
- **[00-INDEX.md](specifications/00-INDEX.md)** - Overview of all specifications
- **[01-PROJECT-OVERVIEW.md](specifications/01-PROJECT-OVERVIEW.md)** - Project goals and architecture
- **[03-BACKEND-SPECIFICATION.md](specifications/03-BACKEND-SPECIFICATION.md)** - Backend API and services
- **[04-FRONTEND-SPECIFICATION.md](specifications/04-FRONTEND-SPECIFICATION.md)** - Frontend components and pages
- **[09-DEPLOYMENT.md](specifications/09-DEPLOYMENT.md)** - Deployment and infrastructure
- **[11-DEPENDENCIES.md](specifications/11-DEPENDENCIES.md)** - Technology stack and dependencies

### Implementation Details
- **Backend API Documentation**: See `backend/app/api/` for endpoint implementations
- **SQL API**: See `backend/app/sql_api/` and `examples/sql_api_demo.py`
- **Preset Integration**: See `backend/app/connectors/preset/README.md`
- **Semantic Models**: See `semantic-models/` for example YAML definitions

### Orchestration
- **[tmux-orchestrator/CLAUDE.md](tmux-orchestrator/CLAUDE.md)** - Complete orchestration protocols and guidelines
- **[tmux-orchestrator/README.md](tmux-orchestrator/README.md)** - Orchestrator system overview

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following [.claude/CLAUDE.md](.claude/CLAUDE.md) guidelines
4. Add tests with good coverage (see `backend/tests/` for examples)
5. Run linters and ensure code quality
6. Commit your changes (`git commit -m 'feat: add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.