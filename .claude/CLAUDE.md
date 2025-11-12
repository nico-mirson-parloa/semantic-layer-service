# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Databricks data transformation project that implements declarative pipelines and Databricks jobs for various data transformation purposes at Parloa, including AMP analytics. The project uses Python 3.12, PySpark, and is deployed via Databricks Asset Bundles.

## Essential Commands

### Linting and Formatting

```bash
make lint-sql          # Lint SQL files with sqlfluff
make fix-sql           # Auto-fix SQL linting errors
make lint-python       # Lint Python with ruff and pyright
make fix-python        # Auto-fix Python linting and formatting
```

### Testing

```bash
make test              # Run all tests with pytest
```

## Architecture

### Activity Schema Pattern

This project implements the **Activity Schema** as the core data modeling technique (see ADR 0005). All analytics queries are built around a unified activity stream table: `amp_all_events_v2` (replacing the legacy `amp_all_events`).

**Key Concepts:**

- **Single source of truth**: `amp_all_events_v2` consolidates events from multiple sources into one chronological stream
- **Self-joins only**: All queries join the activity stream to itself using `conversation_id` (entity) and `event_timestamp`
- **No foreign keys**: Activities are related through entity identifiers and timestamps, not traditional foreign key relationships

**Core columns in activity stream:**

- `tenant_id`: Identifies the tenant
- `conversation_id`: The entity identifier (used for joins)
- `event_source`: Where the event originated
- `event_name`: The activity type
- `event_timestamp`: When the activity occurred (used for joins)
- `event_data`: JSON string with activity-specific attributes

**Querying pattern**: To relate activities, use self-joins with relationships like "first ever", "last before", "first after", "aggregate in between", etc. See ADR 0005 for detailed querying patterns and examples.

### Pipeline Architecture

Declarative pipelines and jobs are defined as Databricks Asset Bundles in the `resources/` directory. Each configuration YAML file defines:

1. **Pipeline/Job configuration**: Declarative pipeline or job settings (catalog, schema, cluster config)
2. **Libraries**: SQL/Python files to execute
3. **Jobs**: Scheduling and orchestration (for non-continuous pipelines)

**Critical**: Tables are tightly coupled to their pipelines. Modifying or deleting a pipeline may cause its tables to be dropped. Always coordinate with data consumers before making pipeline changes.

**Active Pipelines:**

- `amp_metrics_incremental.yml` → tables in `src/amp_metrics_incremental/`
- `amp_billing.yml` → tables in `src/amp_billing/`
- `amp_datahub_transformations.yml` → tables in `src/amp_datahub/`
- `amp_datahub_refresh.yml` → data refresh jobs
- `product_usage.yml` → tables in `src/product_usage/`
- `amp_metrics_incremental_maintenance.yml` → maintenance jobs for incremental metrics

### Directory Structure

```bash
src/                              # SQL and Python transformation code one folder per pipeline/job.
  amp_metrics_incremental/
  amp_billing/
  amp_datahub/
  product_usage/
resources/                        # Databricks Asset Bundle configs
  *.yml                           # Pipeline/job/dashboards etc. definitions
docs/                             # Documentation
  adr/                            # Architecture Decision Records
  data_assets/                    # Table documentation
```

### Finding Table Lineage and Dependencies

**Across Pipelines:**

- Tables reference each other using `${source_catalog}.<schema>.<table>` syntax
- Use Grep to search: `grep -r "schema_name.table_name" src/`
- Example: `grep -r "bronze.amp_all_events_v2" src/` to find all consumers

**Job Task Dependencies:**

- Open the pipeline YAML file in `resources/`
- Look at the `jobs` section → `tasks` array
- Tasks with `depends_on` specify which tasks must complete first
- Example structure:

  ```yaml
  tasks:
    - task_key: task_a
      # runs first
    - task_key: task_b
      depends_on:
        - task_key: task_a  # waits for task_a to complete
  ```

## SQL Style Guide

This project uses **SQLFluff** with strict conventions (see `pyproject.toml`):

- **Indentation**: Always use 4 spaces.
- **Lowercase everything**: Keywords, identifiers, functions, types
- **Trailing commas**: Always use trailing commas
- **Explicit aliasing**: Always alias tables and columns
- **Group by all**: Use `group by all` instead of listing columns
- **CTEs over subqueries**: Prefer CTEs for readability
- **Final CTE pattern**: Always wrap final query in a CTE:

  ```sql
  select *
  from final_cte
  ```

- **Separate aggregations**: Keep aggregations in separate CTEs from scalar operations
- **Cast syntax**: Use `cast(column as datatype)` not `::`
- **Nested field access**: Use `:` for JSON strings, `.` for structs (not `get_json_object`)
- **Where clause format**:
  - If multiple conditions, start with `true`:

    ```sql
    select *
    from table
    where
        true
        and cond1
        and cond2
    ```

  - Otherwise use a single line:

    ```sql
    select *
    from table
    where cond1
    ```

## Databricks Specific Syntax

Every SQL, Python and asset bundle configuration file (`.yml`) should adhere the Databricks documentation:

- Spawn a web-search-researcher subagent in parallel to get the most up to date documentation about the Databricks SQL and Python Language Reference and best practices.
- Spawn a web-search-researcher subagent in parallel to get the most up to date documentation about the Databricks asset bundle configuration and best practices for the specific resource you need to define.
- Spawn a codebase-analyzer subagent in parallel to understand common patterns on how Databricks syntax is used in this repo.

## Table Models Documentation

Every data asset must include:

- `comment` statement describing the table/view in the SQL statement that defines the table/view.
- `comment` statement for each column describing the purpose and meaning of the column.
- Detailed documentation of the whole table in markdown format in the `../docs/models/` in the appropiate folder of the pipeline/job.

## Data Quality Framework

Uses **DQX** (Databricks Labs Data Quality Framework):

- New jobs/pipelines should always have quality checks as part of their flow:
  - Spawn a web-search-researcher subagent in parallel to get the most up to date documentation about the library and how to implement the checks.
  - Spawn a codebase-analyzer subagent in parallel to understand common patterns on how the libary is used in this repo.

- Define checks in YAML files in the same folder of the pipeline/job.
- Apply checks in Python scripts in the same folder of the pipeline/job.

## Development Workflow

### Branch Management

Follow conventional commits with ticket IDs:

- Branch format: `<type>-<ticket-id>-<description>` (e.g., `feat-DPA-123-add-feature`)
- Always create from the updated main branch
- Use `git fetch origin && git checkout main && git pull --ff-only origin main`

### Commit Messages

- Use imperative mood (e.g., "Add fix for dark mode toggle state")
- First line <= 100 characters, body only most relevant highlights.
- Format:

   ```
   <type>(<ticket-id>): <description>

   - Highlights.
   - ...
   ```

- **ONLY USE** this available types when committing:
  - `feat`: New product features.
  - `improve` or `perf`: Improve existing features.
  - `docs`: Documentation.
  - `test`: Test cases.
  - `refactor`: Code refactoring.
  - `ci`: Continuous integration.
  - `fix`: Bug fixes.
  - `chore` or `maintain`: Other changes required to maintain our service level.
  - `build`: Build system or external dependencies.

### Pull Request Process

- Verify first that the branch has been pushed to origin.
  - If it hasn't do the first push using the `--set-upstream` flag.
  - If there are commits that haven't been pushed, you can just use `git push`.

- **ALWAYS create PRs as drafts** using `gh pr create --draft --title "..." --body "..."`.
  - **NEVER FORGET** the `--draft` flag! This allows for review before marking as ready.
  - Title should match the first conventional commit.
  - The Body should follow the following template:

    ```markdown
    ## Purpose of the PR >
  
    [Summary of changes]
  
    ## PR submission checklist
  
    - [ ] Verified data correctness, no anomalies (add screenshots)
    - [ ] Added `comment` statements to new/modified columns and tables
    - [ ] Added markdown documentation in `./docs/` folder
    - [ ] Validated pipelines in both WEU and EUS regions
    - [ ] Added screenshots or links to validated pipelines

    ```

- **ALWAYS** open the PR after creating it.
