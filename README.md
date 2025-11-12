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

#### Advanced Features (Phase 2)
- **✅ Automatic Model Generation**: AI-powered generation from gold layer tables
  - Intelligent pattern recognition and analysis
  - Industry-specific metric suggestions with confidence scoring
  - Interactive customization wizard
  - One-click YAML generation and validation
- **🚧 Documentation Generation**: Auto-generate comprehensive documentation
  - Multiple export formats (Markdown, HTML, PDF, Confluence)
  - Template system for different audiences
  - Usage examples and best practices
- **📋 Lineage Visualization**: Interactive data lineage tracking
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
├── docs/                  # Documentation and specs
└── docker-compose.yml     # Local development setup
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

### Using the Orchestrator

1. **Start the orchestrator session**:
   ```bash
   cd tmux-orchestrator
   ./setup_tmux_orchestrator.sh
   ```

2. **Attach to the session**:
   ```bash
   tmux attach-session -t semantic
   ```

3. **Navigate between windows**:
   - `Ctrl+b 0-9`: Switch to window 0-9
   - `Ctrl+b n`: Next window
   - `Ctrl+b p`: Previous window
   - `Ctrl+b w`: List all windows

4. **Communicate with agents**:
   ```bash
   # From orchestrator window, send messages to other agents
   ./send-claude-message.sh semantic:2 "Please implement the authentication endpoint"
   ```

5. **Monitor agent work**:
   ```bash
   # Capture output from an agent's window
   tmux capture-pane -t semantic:2 -p | tail -50
   ```

### Benefits

- **Parallel Development**: Multiple agents work simultaneously on different parts
- **24/7 Development**: Agents can work continuously without breaks
- **Quality Assurance**: PM agent ensures high standards are maintained
- **Clear Communication**: Structured messaging protocols prevent confusion
- **Coordinated Workflow**: Orchestrator manages dependencies and priorities

### Best Practices

1. **Regular Status Updates**: Agents report progress every 30 minutes
2. **Commit Frequently**: Auto-commit every 30 minutes to prevent work loss
3. **Use Feature Branches**: Each major task gets its own branch
4. **Quality Gates**: PM reviews all work before merging
5. **Clear Communication**: Use structured message templates

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

See [SQL API Guide](docs/SQL_API_GUIDE.md) for detailed documentation.

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

See [Preset Integration Guide](docs/PRESET_INTEGRATION_GUIDE.md) for complete setup instructions.

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

## Development Roadmap

### Phase 1: Foundation (Current)
- [ ] Project structure setup
- [ ] Basic Databricks connectivity
- [ ] Simple semantic model parser

### Phase 2: Core Features
- [ ] Metadata discovery from Unity Catalog
- [ ] Interactive model builder UI
- [ ] Query execution engine

### Phase 3: Advanced Features
- [ ] Automatic model generation
- [ ] Documentation generation
- [ ] Lineage visualization
- [ ] Performance optimization

### Phase 4: Enterprise Features
- [ ] Multi-tenant support
- [ ] Role-based access control
- [ ] Advanced caching strategies
- [ ] API rate limiting

## 📚 Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get up and running quickly
- **[Development Guide](docs/DEVELOPMENT.md)** - Development setup and workflow
- **[API Reference](docs/API_REFERENCE.md)** - Complete REST API documentation
- **[SQL API Guide](docs/SQL_API_GUIDE.md)** - PostgreSQL-compatible SQL interface
- **[Preset Integration Guide](docs/PRESET_INTEGRATION_GUIDE.md)** - Connect Preset BI platform
- **[Testing Guide](docs/TESTING_GUIDE.md)** - Testing strategy and best practices
- **[Semantic Layer Guide](docs/SEMANTIC_LAYER_GUIDE.md)** - Core concepts and implementation
- **[Frontend Specification](docs/FRONTEND_SPEC.md)** - UI component specifications

See the [Documentation Index](docs/README.md) for a complete list of available documentation.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the [Development Guide](docs/DEVELOPMENT.md)
4. Add tests with good coverage (see [Testing Guide](docs/TESTING_GUIDE.md))
5. Commit your changes (`git commit -m 'feat: add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.