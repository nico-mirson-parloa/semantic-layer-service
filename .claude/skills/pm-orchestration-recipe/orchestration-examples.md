# PM Orchestration Examples

## Example 1: Sequential Research → Implementation

### User Request
"Add a new metric to track conversation resolution time"

### Step 1: Requirements Gathering

```markdown
## Questions Asked

1. **Scope**: All conversations or specific conversation types?
2. **Definition**: Resolution = conversation_end or specific event?
3. **Granularity**: Per conversation, aggregated by day/week?
4. **Dependencies**: Which dashboards/reports consume this?
5. **Quality**: What validation rules ensure accuracy?

## User Responses

1. All conversations in amp_all_events_v2
2. Resolution = event_name = 'conversation.closed'
3. Both - base table per conversation, aggregated views for reporting
4. AMP Billing dashboard, Customer Success reports
5. Must validate: no null resolution times, resolution after start
```

### Step 2: Specification Creation

```markdown
## Problem Statement
Add conversation resolution time metric to track time from conversation start to conversation.closed event

## Success Criteria
- [ ] Base table with per-conversation resolution time in bronze layer
- [ ] Aggregated view by day/tenant in silver layer
- [ ] DQX checks validate data quality
- [ ] Documentation in docs/models/amp_metrics_incremental/
- [ ] Linting passes

## Technical Approach
Activity Schema self-join:
- Join amp_all_events_v2 to itself on conversation_id
- First event (conversation.started) → Last event (conversation.closed)
- Calculate time_diff in minutes

## Data Quality Requirements
- No null resolution times (DQX check)
- Resolution timestamp > start timestamp (DQX check)
- All conversations have start event (DQX check)

## Acceptance Criteria
- [ ] SQL file: src/amp_metrics_incremental/conversation_resolution_time.sql
- [ ] Pipeline config updated: resources/amp_metrics_incremental.yml
- [ ] DQX checks: src/amp_metrics_incremental/dqx_conversation_resolution.yml
- [ ] Documentation: docs/models/amp_metrics_incremental/conversation_resolution_time.md
- [ ] Tests pass: make test
- [ ] Linting clean: make lint-sql
```

### Step 3: Agent Delegation (Sequential)

```python
# Agent 1: Research existing patterns
Task(
  subagent_type="codebase-analyzer",
  prompt="""
    Find existing conversation metrics in amp_metrics_incremental.

    Return:
    1. File paths for similar metrics
    2. Activity Schema join patterns used
    3. DQX check examples
    4. Documentation structure
  """,
  model="haiku"
)

# Wait for result, then use findings in next prompt

# Agent 2: Implement based on patterns
Task(
  subagent_type="databricks-genius",
  prompt=f"""
    Implement conversation resolution time metric.

    Specification:
    {specification}

    Existing patterns to follow:
    {agent_results[0].output.patterns}

    Create:
    1. SQL file following Activity Schema patterns
    2. DQX YAML configuration
    3. DQX Python apply script
    4. Table documentation
  """,
  model="sonnet"
)

# Agent 3: Review implementation
Task(
  subagent_type="production-code-reviewer",
  prompt=f"""
    Review implementation against specification.

    Specification:
    {specification}

    Files:
    - src/amp_metrics_incremental/conversation_resolution_time.sql
    - src/amp_metrics_incremental/dqx_conversation_resolution.yml
    - src/amp_metrics_incremental/apply_dqx_checks.py
    - docs/models/amp_metrics_incremental/conversation_resolution_time.md

    Verify:
    - Activity Schema self-join correct
    - DQX checks comprehensive
    - Documentation complete
    - SQL style compliance
  """
)
```

### Step 4: Review Results

```markdown
## Review Results: Conversation Resolution Time Metric

### ✓ Passed
- Activity Schema pattern: Correct self-join on conversation_id
- DQX checks: All 3 quality rules implemented
- Documentation: Complete with examples
- SQL style: All SQLFluff rules followed

### ✗ Failed
- Pipeline config: Missing library entry in resources/amp_metrics_incremental.yml
  - **Expected**: Library entry for new SQL file
  - **Actual**: File not referenced in pipeline
  - **Fix**: Add to libraries section in YAML

### Next Steps
1. Add library entry to pipeline config
2. Re-run production-code-reviewer
3. Run make lint-sql to verify
4. Create PR as draft
```

## Example 2: Parallel Research

### User Request
"We need to optimize the amp_billing pipeline - it's taking too long"

### Step 1: Requirements Gathering

```markdown
## Questions Asked

1. **Current state**: What's the current runtime?
2. **Target**: What's acceptable runtime?
3. **Bottleneck**: Which specific queries/tables are slow?
4. **Data volume**: How much data processed?
5. **Priority**: Speed vs cost vs data freshness?

## User Responses

1. 45 minutes end-to-end
2. Under 20 minutes
3. Not sure - need investigation
4. ~10M events/day
5. Speed is priority, cost secondary
```

### Step 2: Investigation (Parallel Agents)

```python
# Single message with 3 parallel Task calls

# Agent 1: Analyze codebase
Task(
  subagent_type="codebase-analyzer",
  prompt="""
    Analyze amp_billing pipeline performance.

    Find:
    1. All SQL files in src/amp_billing/
    2. Complex joins or aggregations
    3. Table dependencies (which tables read from which)
    4. Partition strategies used

    Return file paths and code snippets showing expensive operations.
  """,
  model="haiku"
)

# Agent 2: Research Databricks optimization
Task(
  subagent_type="web-search-researcher",
  prompt="""
    Research Databricks Delta Live Tables optimization techniques.

    Find:
    1. Best practices for large-scale aggregations
    2. Partition strategy recommendations
    3. Streaming vs batch table trade-offs
    4. Z-ordering strategies

    Focus on official Databricks documentation 2024-2025.
  """,
  model="haiku"
)

# Agent 3: Check Databricks-specific patterns
Task(
  subagent_type="databricks-genius",
  prompt="""
    Identify Databricks-specific optimization opportunities for amp_billing.

    Review:
    1. Current cluster configuration in resources/amp_billing.yml
    2. Table types (streaming vs materialized)
    3. Expectations (DQX) overhead
    4. Catalog/schema performance settings

    Return specific Databricks recommendations.
  """,
  model="haiku"
)
```

### Step 3: Aggregate Findings

```markdown
## Investigation Results

### Codebase Analysis (codebase-analyzer)
**Bottleneck identified**: `conversation_billing_summary.sql`
- Full table scan on amp_all_events_v2 (10M rows)
- Complex multi-way join (5 tables)
- No partition pruning on event_timestamp
- File: src/amp_billing/conversation_billing_summary.sql:45

### Databricks Best Practices (web-search-researcher)
**Key findings**:
1. Partition by date column for time-series queries
2. Z-order by high-cardinality join columns
3. Use streaming tables for append-only data
4. OPTIMIZE command after large writes

### Databricks-Specific (databricks-genius)
**Recommendations**:
1. Change amp_all_events_v2 query to streaming table consumption
2. Add partition filter: WHERE event_timestamp >= current_date - interval 90 days
3. Increase cluster workers from 2 to 4 for parallel processing
4. Enable auto-optimization in pipeline config
```

### Step 4: Specification Creation

```markdown
## Problem Statement
Reduce amp_billing pipeline runtime from 45min to <20min by optimizing conversation_billing_summary.sql

## Success Criteria
- [ ] Pipeline completes in <20 minutes
- [ ] Data correctness maintained (verify with existing DQX checks)
- [ ] Cost increase <20%

## Technical Approach
1. Add partition filter (90-day window)
2. Convert to streaming table consumption
3. Increase cluster size (2→4 workers)
4. Enable auto-optimization

## Acceptance Criteria
- [ ] conversation_billing_summary.sql updated with partition filter
- [ ] Pipeline config cluster size increased
- [ ] Auto-optimization enabled in YAML
- [ ] Tested in dev environment with runtime measurement
- [ ] DQX checks pass
- [ ] Documentation updated with optimization rationale
```

## Example 3: Conditional Review Gate

### User Request
"Create PR for new customer churn prediction model"

### Step 1: Pre-Review Specification

```markdown
## Acceptance Criteria
- [ ] Production code passes code review
- [ ] Test code passes test review
- [ ] Architecture follows hexagonal principles
- [ ] Documentation complete
- [ ] All tests pass
- [ ] Linting clean
```

### Step 2: Parallel Reviews

```python
# Single message with 3 parallel reviews

Task(
  subagent_type="production-code-reviewer",
  prompt="""
    Review production code for customer churn model.

    Files: src/product_usage/churn_prediction.sql

    Check:
    - SQL style compliance
    - Activity Schema patterns
    - Data quality checks
  """
)

Task(
  subagent_type="test-code-reviewer",
  prompt="""
    Review test code for customer churn model.

    Files: test/product_usage/test_churn_prediction.py

    Check:
    - Test coverage
    - Test helpers usage
    - Assertions quality
  """
)

Task(
  subagent_type="architecture-reviewer",
  prompt="""
    Review architecture for customer churn model.

    Files:
    - src/product_usage/churn_prediction.sql
    - resources/product_usage.yml

    Check:
    - Layer boundaries
    - Dependency rules
    - Hexagonal principles
  """
)
```

### Step 3: Conditional Logic

```python
# Aggregate results
prod_violations = agent_results[0].output.violations
test_violations = agent_results[1].output.violations
arch_violations = agent_results[2].output.violations

total_critical = (
  prod_violations.filter(v => v.severity === 'critical').length +
  test_violations.filter(v => v.severity === 'critical').length +
  arch_violations.filter(v => v.severity === 'critical').length
)

if total_critical > 0:
  # ABORT - Critical issues must be fixed
  return {
    "status": "BLOCKED",
    "reason": "Critical violations found",
    "violations": [prod_violations, test_violations, arch_violations],
    "next_steps": [
      "Fix all critical violations",
      "Re-run reviews",
      "Do not create PR until clean"
    ]
  }
else:
  # PROCEED - Create PR
  Task(
    subagent_type="github-recipe",
    prompt="""
      Create draft PR for customer churn model.

      Title: feat(DPA-456): Add customer churn prediction model

      Body:
      ## Purpose of the PR
      Implements customer churn prediction using activity patterns

      ## PR submission checklist
      - [x] Verified data correctness
      - [x] Added comments to columns/tables
      - [x] Added markdown documentation
      - [x] All reviews passed

      Branch: feat-DPA-456-churn-model
      Base: main
    """
  )
```

## Example 4: Handling Ambiguity

### User Request
"Add lineage tracking"

### Step 1: Identify Ambiguity

```
"lineage tracking" could mean:
1. Unity Catalog lineage (table→table dependencies)
2. Data lineage (row-level tracking)
3. Query lineage (which queries access which data)
4. Pipeline lineage (job→task dependencies)
```

### Step 2: Ask Clarifying Questions

```python
AskUserQuestion(
  questions=[
    {
      "question": "What type of lineage tracking do you need?",
      "header": "Lineage Type",
      "multiSelect": false,
      "options": [
        {
          "label": "Table Lineage",
          "description": "Track which tables are created from which sources (Unity Catalog level)"
        },
        {
          "label": "Row Lineage",
          "description": "Track individual record transformations through pipeline stages"
        },
        {
          "label": "Query Lineage",
          "description": "Track which queries/dashboards consume which tables"
        },
        {
          "label": "Pipeline Lineage",
          "description": "Track job task dependencies and execution flow"
        }
      ]
    },
    {
      "question": "What's the primary use case?",
      "header": "Use Case",
      "multiSelect": false,
      "options": [
        {
          "label": "Compliance",
          "description": "Regulatory requirements for data traceability"
        },
        {
          "label": "Impact Analysis",
          "description": "Understand downstream effects of schema changes"
        },
        {
          "label": "Debugging",
          "description": "Trace data quality issues to source"
        },
        {
          "label": "Documentation",
          "description": "Visualize data flow for stakeholders"
        }
      ]
    }
  ]
)
```

### Step 3: User Response → Refined Specification

```markdown
## User Selections
1. Table Lineage (Unity Catalog level)
2. Impact Analysis (understand downstream effects)

## Refined Problem Statement
Implement automated table lineage tracking using Unity Catalog to enable impact analysis when modifying amp_all_events_v2 schema.

## Success Criteria
- [ ] Lineage captured for all tables in amp_metrics_incremental pipeline
- [ ] API endpoint returns lineage for given table
- [ ] Documentation shows how to query lineage
- [ ] Lineage updates automatically when pipeline runs

## Technical Approach
Use Databricks Unity Catalog INFORMATION_SCHEMA:
1. Query table_lineage system table
2. Create view exposing upstream/downstream dependencies
3. Add to semantic layer API for querying
```

## Example 5: Escalation

### User Request
"Fix the failing pipeline"

### Step 1: Investigation

```python
# Research which pipeline is failing
Task(
  subagent_type="codebase-analyzer",
  prompt="""
    Search for recent pipeline failures in logs or configs.
    Check resources/*.yml for any obvious misconfigurations.
  """
)
```

### Step 2: Escalation Trigger

```markdown
## Findings
Multiple pipelines showing failures:
- amp_metrics_incremental: Stuck in PENDING state
- amp_billing: Cluster creation timeout
- product_usage: Schema not found error

## Escalation Reason
Cannot determine which pipeline user wants fixed - multiple failures present.
Each requires different fix approach.
```

### Step 3: Escalation Response

```python
AskUserQuestion(
  questions=[
    {
      "question": "Which pipeline failure should I prioritize?",
      "header": "Pipeline",
      "multiSelect": false,
      "options": [
        {
          "label": "amp_metrics_incremental",
          "description": "Status: PENDING (possibly resource contention)"
        },
        {
          "label": "amp_billing",
          "description": "Error: Cluster creation timeout (infrastructure issue)"
        },
        {
          "label": "product_usage",
          "description": "Error: Schema not found (configuration issue)"
        }
      ]
    }
  ]
)
```

### Step 4: Focused Fix

```markdown
## User Selected: product_usage (schema not found)

## Specification
Fix product_usage pipeline schema not found error

## Investigation Steps
1. Check resources/product_usage.yml catalog/schema config
2. Verify schema exists in Unity Catalog
3. Check permissions on schema
4. Review recent changes to pipeline config

## Acceptance Criteria
- [ ] Pipeline runs successfully
- [ ] Schema configuration correct
- [ ] Permissions verified
- [ ] Root cause documented
```

## Example 6: Scope Creep Prevention

### User Request
"Add NPS score tracking to amp_metrics_incremental"

### During Implementation
User adds: "Oh and also add customer satisfaction trends"
User adds: "Can we also show retention cohorts?"
User adds: "And predict churn probability"

### Specification Enforcement

```markdown
## Original Specification
**Scope**: NPS score tracking
- Calculate NPS from survey responses
- Store in amp_metrics_incremental pipeline
- Add to semantic layer API

## Scope Creep Detected
User requested additional features during implementation:
1. Customer satisfaction trends (new feature)
2. Retention cohorts (new feature)
3. Churn prediction (ML feature - significant scope change)

## Response
"These are valuable features, but they're outside the original specification for NPS tracking.

Let's complete the NPS tracking first, then I can help you with the additional features in separate, well-specified tasks:

1. **Current task**: NPS score tracking
   - ETA: Today
   - Files: 2 SQL files, 1 doc

2. **Proposed task 2**: Customer satisfaction trends
   - Scope: TBD (needs requirements gathering)
   - Dependencies: NPS tracking (task 1)

3. **Proposed task 3**: Retention cohorts
   - Scope: TBD (needs requirements gathering)
   - Dependencies: None

4. **Proposed task 4**: Churn prediction
   - Scope: ML model (significant effort)
   - Dependencies: Satisfaction + retention data

Would you like to:
A) Complete NPS tracking first, then discuss additional features
B) Pause and redefine scope to include all features
C) Prioritize which features are most important"
```

## Validation Pattern for All Examples

Every example follows:

```
1_ User request → Assess specificity
2_ Vague? → Ask questions | Specific? → Document spec
3_ Get user approval on spec
4_ Delegate to agents with context
5_ Monitor progress
6_ Review outputs against acceptance criteria
7_ ✓ Pass → Deliver | ✗ Fail → Feedback → Re-delegate
8_ Confirm completion with user
```
