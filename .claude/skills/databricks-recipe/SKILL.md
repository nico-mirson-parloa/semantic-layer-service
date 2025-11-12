---
name: reviewing-databricks-recipe
description: Reviews Databricks configurations, SQL, Python code, and architecture patterns using official documentation and best practices. Use when working with Databricks pipelines, SQL, Python transformations, asset bundles, or designing data architecture.
---

# Databricks Review Recipe

## Quick Reference

```bash
databricks bundle validate
databricks bundle deploy -t dev
make lint-sql
make lint-python
```

| Resource | Pattern |
|----------|---------|
| SQL | Activity schema, self-joins, lowercase keywords |
| Python | PySpark patterns, DQX quality checks |
| Bundles | YAML configs in resources/ |
| Architecture | Medallion (bronze→silver→gold) |

## When to Use

- Reviewing Databricks SQL/Python code
- Designing data pipelines
- Validating asset bundle configurations
- Architecture decisions (tables, schemas, jobs)
- User mentions: Databricks, DLT, pipelines, asset bundles, PySpark

## Documentation Fetch Protocol

**ALWAYS spawn web-search-researcher in parallel for latest docs:**

```bash
Web search: "Databricks SQL language reference 2025"
Web search: "Databricks asset bundles best practices"
Web search: "Databricks {specific_feature} documentation"
```

**Resources:**
- Getting started: https://docs.databricks.com/aws/en/getting-started/
- SQL reference: https://docs.databricks.com/aws/en/sql/language-manual/
- Asset bundles: https://docs.databricks.com/aws/en/dev-tools/bundles/
- Architecture patterns: https://www.databricks.com/resources/architectures

## SQL Review Checklist

- [ ] Lowercase keywords → `select` not `SELECT`
- [ ] Activity schema → Self-join on `conversation_id` + `event_timestamp`
- [ ] CTE over subqueries → Named CTEs for intermediate steps
- [ ] Final CTE pattern → Always wrap final query
- [ ] Trailing commas → Always use
- [ ] Group by all → Not listing columns
- [ ] Nested access → `:` for JSON strings, `.` for structs
- [ ] Cast syntax → `cast(x as type)` not `::`
- [ ] Where clause → Multiple conditions start with `true`
- [ ] Table comments → `comment` statement for table and columns
- [ ] Documentation → Markdown file in docs/models/

See [sql-reference.md](sql-reference.md) for style guide and SQL functions.

## Python Review Checklist

- [ ] PySpark imports → `from pyspark.sql import functions as F`
- [ ] DQX quality checks → YAML + Python apply script
- [ ] Error handling → Try/except with logging
- [ ] Type hints → All function signatures
- [ ] Docstrings → Google style format

See [pyspark-reference.md](pyspark-reference.md) for PySpark patterns and examples.

## Asset Bundle Review Checklist

- [ ] Valid YAML → No tabs, proper indentation
- [ ] Catalog/schema → `${source_catalog}.schema.table` syntax
- [ ] Cluster configs → Instance types, runtime version
- [ ] Dependencies → `depends_on` for task ordering
- [ ] Libraries → Correct paths to SQL/Python files

## Architecture Patterns

| Pattern | When | Structure |
|---------|------|-----------|
| Medallion | ETL/ELT pipelines | bronze (raw) → silver (cleaned) → gold (aggregated) |
| Activity Schema | Event analytics | Single activity stream + self-joins |
| Star Schema | BI/Reporting | Fact tables + dimension tables |
| Data Vault | Enterprise DW | Hubs, links, satellites |

**Decision tree:**
```
Data type?
├─ Event stream → Activity Schema
├─ Analytics/BI → Star Schema
├─ Enterprise DW → Data Vault
└─ General ETL → Medallion
```

## Activity Schema Pattern

**Core principle**: Single activity stream → Self-join only

**Activity stream structure:**
```sql
select
    tenant_id,
    conversation_id,  -- Entity for joins
    event_source,
    event_name,
    event_timestamp,  -- Temporal ordering
    event_data        -- JSON string
from bronze.amp_all_events_v2
```

**Join patterns:**

| Relationship | Pattern |
|--------------|---------|
| First ever | `min(event_timestamp)` by entity |
| Last before | `max(event_timestamp where timestamp < anchor)` |
| First after | `min(event_timestamp where timestamp > anchor)` |
| Between | `where timestamp between start and end` |
| Aggregate | `count/sum/avg over window` |

**Basic example:**
```sql
with conversation_starts as (
    select
        conversation_id,
        min(event_timestamp) as start_time
    from bronze.amp_all_events_v2
    where event_name = 'conversation_started'
    group by all
),

first_user_message as (
    select
        e.conversation_id,
        min(e.event_timestamp) as first_msg_time
    from bronze.amp_all_events_v2 as e
    inner join conversation_starts as cs
        on e.conversation_id = cs.conversation_id
    where
        true
        and e.event_name = 'user_message'
        and e.event_timestamp > cs.start_time
    group by all
),

final_cte as (
    select *
    from first_user_message
)

select *
from final_cte
```

See [sql-reference.md](sql-reference.md) for advanced activity schema examples.

## Pipeline Configuration

**Structure:**
```
resources/
├── pipeline_name.yml       # Config
src/
├── pipeline_name/
    ├── table_01.sql        # Transformations
    ├── table_02.py
    ├── quality_checks.yml  # DQX
    └── apply_checks.py
docs/
├── models/
    └── pipeline_name/
        └── table_01.md     # Documentation
```

**Pipeline config:**
```yaml
resources:
  pipelines:
    pipeline_name:
      name: pipeline_name
      catalog: ${source_catalog}
      target: schema_name
      libraries:
        - file:
            path: ../src/pipeline_name/table_01.sql
      clusters:
        - label: default
          spark_version: 15.4.x-scala2.12
          node_type_id: Standard_DS3_v2
          num_workers: 2
```

**Job config with dependencies:**
```yaml
resources:
  jobs:
    job_name:
      name: job_name
      tasks:
        - task_key: task_a
          python_wheel_task:
            package_name: package
            entry_point: main

        - task_key: task_b
          depends_on:
            - task_key: task_a
          notebook_task:
            notebook_path: ../src/notebook.py
```

## DQX Quality Framework

**Define checks (quality_checks.yml):**
```yaml
checks:
  - name: no_nulls_in_id
    table: schema.table_name
    check: id IS NOT NULL
    severity: critical

  - name: positive_amounts
    table: schema.table_name
    check: amount > 0
    severity: error
```

**Apply checks (apply_checks.py):**
```python
from databricks.labs.dqx import DQX

dqx = DQX(spark)
results = dqx.run_checks("quality_checks.yml")

if results.has_critical_failures():
    raise Exception("Critical data quality failures")
```

**Severity levels:**

| Severity | Action |
|----------|--------|
| critical | Fail pipeline immediately |
| error | Log and alert, continue |
| warning | Log only |

See [pyspark-reference.md](pyspark-reference.md) for DQX integration examples.

## Common Issues & Fixes

| Issue | Fix | Validation |
|-------|-----|------------|
| SQL uppercase | Lowercase all keywords | `make lint-sql` pass |
| Missing trailing comma | Add comma after last item | SQLFluff pass |
| Subquery instead of CTE | Convert to named CTE | Readability improved |
| Direct JSON access | Use `:` for JSON strings | Syntax valid |
| Missing table comments | Add `comment` statement | Documentation exists |
| No DQX checks | Add YAML + Python script | Quality validated |
| Cast with `::` | Use `cast(x as type)` | SQLFluff pass |
| Verbose where clause | Start with `true` if multiple conditions | SQLFluff pass |
| Group by listing | Use `group by all` | SQLFluff pass |

## Table Documentation

**SQL comment statements:**
```sql
create or replace table schema.table_name
comment 'Description of table purpose and contents'
as
select
    column_a comment 'Description of column_a',
    column_b comment 'Description of column_b',
from source
```

**Markdown documentation (docs/models/pipeline_name/table_name.md):**
```markdown
# Table Name

## Purpose
Brief description of table purpose

## Schema
| Column | Type | Description |
|--------|------|-------------|
| column_a | string | Details |
| column_b | int | Details |

## Upstream Dependencies
- source_table_1
- source_table_2

## Downstream Consumers
- consumer_table_1
- dashboard_name

## Refresh Schedule
Hourly / Daily / On-demand

## Data Quality Rules
- No nulls in primary key
- Amounts must be positive
```

## Finding Dependencies

**Upstream dependencies (what this table reads):**
```bash
# Search for table references in SQL
grep -r "schema_name.table_name" src/pipeline_name/

# Search for catalog references
grep -r "bronze.amp_all_events_v2" src/
```

**Downstream dependencies (what reads this table):**
```bash
# Search where this table is referenced
grep -r "schema_name.table_name" src/
```

**Job task dependencies:**
```yaml
# In pipeline YAML, look for depends_on
tasks:
  - task_key: task_a
    # runs first

  - task_key: task_b
    depends_on:
      - task_key: task_a  # waits for task_a
```

## Validation Workflow

**After creating/reviewing Databricks code:**

| Phase | Action | Command |
|-------|--------|---------|
| 1. Syntax | Validate SQL/Python | `make lint-sql && make lint-python` |
| 2. Bundle | Validate YAML | `databricks bundle validate` |
| 3. Logic | Activity schema? Self-joins correct? | Manual review |
| 4. Docs | Comments + markdown exist? | Check files |
| 5. Quality | DQX checks defined? | Check YAML exists |

**Evidence gathering:**
```
VALIDATION REPORT:
✓ SQL syntax: SQLFluff pass [Evidence] make lint-sql output
✓ Python syntax: Ruff pass [Evidence] make lint-python output
✓ Bundle valid: [Evidence] databricks bundle validate output
✓ Activity schema: Self-joins on conversation_id [Evidence] Lines 10-25
✓ Documentation: Comments added [Evidence] table_name.sql:5, table_name.md exists
✓ Quality checks: YAML defined [Evidence] quality_checks.yml exists

✗ FAIL: Missing trailing comma [Evidence] Line 42
✗ FAIL: Using :: instead of cast [Evidence] Line 67

VIOLATIONS (2):
1. Line 42: Add trailing comma
2. Line 67: Replace :: with cast()

ACTION: Fix violations and re-validate
```

## Architecture Decision Process

**When designing data architecture:**

1. **Fetch latest docs:**
   ```bash
   # Spawn web-search-researcher in parallel
   Web search: "Databricks medallion architecture 2025"
   Web search: "Databricks activity schema pattern"
   Web search: "Databricks {architecture_name} best practices"
   ```

2. **Analyze codebase:**
   ```bash
   # Spawn codebase-analyzer in parallel
   Task: Find existing pipeline patterns
   Task: Identify common table structures
   ```

3. **Choose pattern:**
   ```
   Event stream? → Activity Schema
   Analytics? → Star Schema
   ETL? → Medallion
   Enterprise? → Data Vault
   ```

4. **Document decision:**
   ```bash
   # Create ADR in docs/adr/
   NNNN-architecture-pattern-name.md
   ```

## Critical Pipeline Rules

**Table-pipeline coupling:**
- Modifying pipeline → May drop tables
- Deleting pipeline → Drops all tables
- Coordinate with consumers before changes

**Validation before changes:**
```bash
# Find downstream consumers
grep -r "schema.table_name" src/

# Check Databricks lineage
# Use Databricks UI: Data → Tables → Lineage tab
```

**Deployment order:**
```
1. Create branch: feature/DPA-XXX-description
2. Test in dev: databricks bundle deploy -t dev
3. Validate tables created
4. Create draft PR: gh pr create --draft
5. Review and merge
6. Deploy to prod: databricks bundle deploy -t prod
```

## BEFORE Saving (Validation)

```
VALIDATE:
- [ ] SQL lowercase? Trailing commas? Final CTE?
- [ ] Activity schema followed? Self-joins only?
- [ ] Python type hints? DQX checks?
- [ ] Asset bundle valid YAML? Dependencies correct?
- [ ] Documentation added? Comments + markdown?
- [ ] Latest Databricks docs consulted?
- [ ] Codebase patterns followed?
- [ ] Quality checks defined? Applied?
- [ ] Dependencies identified? Documented?
- [ ] Validation commands run? All pass?

IF all pass → Deploy
IF any fail → Fix and re-validate
```

**No deployment without validation.**
