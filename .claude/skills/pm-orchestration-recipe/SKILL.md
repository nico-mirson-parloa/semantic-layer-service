---
name: orchestrating-pm-recipe
description: Orchestrates requirements gathering, specification creation, agent coordination, and work review. Use when managing complex tasks requiring specification-driven development.
---

# PM Orchestration Recipe

## Quick Reference

```
Vague requirement → Ask questions → Document spec → Delegate → Review → Deliver
```

## When to Use

- Starting new task/feature requiring clear requirements
- User provides ambiguous/vague request
- Multiple agents needed for complex task
- Reviewing completed work against specifications
- Breaking down large tasks into actionable items

## Requirement Gathering Patterns

### Specificity Assessment

```
requirement → specific? → document | vague? → ask_questions
```

**Question categories:**
- **Scope**: What's included/excluded?
- **Edge cases**: What happens when [scenario]?
- **Dependencies**: What relies on this? What does this rely on?
- **Success**: How do we measure completion?
- **Constraints**: What limitations exist?

### Example Question Flow

```
User: "Make reporting faster"

Ask:
1. Which reports? (scope)
2. Current speed vs target? (measurable)
3. Bottleneck identified? (technical)
4. User-facing or backend? (approach)
5. Data correctness priority? (trade-offs)
```

## Specification Template

```markdown
## Problem Statement
[Clear description of what needs solving]

## Success Criteria
- [ ] Measurable outcome 1
- [ ] Measurable outcome 2
- [ ] Measurable outcome 3

## Technical Approach
[Aligned with project patterns - Activity Schema, DQX, etc.]

## Dependencies
- Upstream: [What this relies on]
- Downstream: [What relies on this]

## Data Quality Requirements
[DQX checks needed]

## Acceptance Criteria
- [ ] Functional requirement 1
- [ ] Functional requirement 2
- [ ] Non-functional requirement 3
- [ ] Documentation complete
- [ ] Tests pass
- [ ] Linting clean

## Artifacts Required
- [ ] Code files: [list]
- [ ] Documentation: [list]
- [ ] Tests: [list]
- [ ] Quality checks: [list]
```

## Agent Delegation Patterns

### Sequential Pattern

```
research → design → implement → test → review
```

**When to use:** Dependencies between steps
**How:** Pass previous results to next agent

```
Agent A output → Agent B context.findings
Agent B output → Agent C context.design
```

### Parallel Pattern

```
codebase-analyzer ┐
web-researcher    ├→ Aggregate findings
databricks-genius ┘
```

**When to use:** Independent research tasks
**How:** Single message with multiple Task calls

```python
# Single message block
Task(subagent_type="codebase-analyzer", ...)
Task(subagent_type="web-search-researcher", ...)
Task(subagent_type="databricks-genius", ...)
```

### Conditional Pattern

```
security-review → PASS → merge | FAIL → fix → re-review
```

**When to use:** Validation gates
**How:** Check output before proceeding

```
result.violations.length === 0 → proceed | > 0 → abort
```

## Agent Coordination Context

### Context Structure

```json
{
  "specification": "Full spec text",
  "pr_number": 123,
  "files": ["path/to/file.sql"],
  "repository": "semantic-layer-service",
  "requirements": {
    "functional": ["req1", "req2"],
    "nonfunctional": ["req3", "req4"]
  },
  "acceptance_criteria": ["ac1", "ac2"]
}
```

### Passing Context

```python
# To next agent
Task(
  subagent_type="production-code-reviewer",
  prompt=f"""
    Review implementation against specification.

    Specification:
    {specification}

    Files changed:
    {files}

    Verify:
    - All acceptance criteria met
    - Project standards followed
    - Documentation complete
  """
)
```

## Review Patterns

### Pre-Review Checklist

```
- [ ] All acceptance criteria listed?
- [ ] Measurable success criteria defined?
- [ ] Project patterns documented (Activity Schema, DQX, etc.)?
- [ ] Dependencies identified?
```

### Review Workflow

```
1_ Gather: Collect all agent outputs
2_ Check: Verify against acceptance criteria
3_ Validate: Check project standards
4_ Report: ✓ ALL pass → approve | ✗ ANY fail → actionable feedback
```

### Acceptance Criteria Verification

| Criterion | Check | Evidence |
|-----------|-------|----------|
| Functional | Feature works | Test results |
| Documentation | Docs exist | Markdown files + SQL comments |
| Quality | Checks pass | DQX results |
| Standards | Linting clean | `make lint-*` output |
| Tests | Tests pass | `make test` output |

### Feedback Template

```markdown
## Review Results: [Feature Name]

### ✓ Passed
- [Criterion]: [Evidence]

### ✗ Failed
- [Criterion]: [Issue found]
  - **Expected**: [What spec says]
  - **Actual**: [What was delivered]
  - **Fix**: [Actionable step]

### Next Steps
1. [Action item 1]
2. [Action item 2]
```

## Decision-Making Framework

### Before Delegating

```
✓ Spec documented?
✓ Success criteria measurable?
✓ Dependencies identified?
✓ User agreement?
→ Delegate | ✗ ANY → Clarify first
```

### When Reviewing

```
✓ Acceptance criteria met?
✓ Project standards followed?
✓ Artifacts present?
✓ Production-ready?
→ Approve | ✗ ANY → Request changes
```

### When Encountering Ambiguity

```
1_ List possible interpretations
2_ Assess risks of each
3_ Draft clarifying questions
4_ Options or propose? → propose single | present multiple
```

## Project-Specific Patterns

### Databricks Context

When delegating Databricks tasks:

```json
{
  "patterns": {
    "activity_schema": "amp_all_events_v2 self-joins",
    "pipelines": "resources/*.yml",
    "sql_style": "SQLFluff strict",
    "quality": "DQX framework",
    "docs": "SQL comments + docs/models/"
  }
}
```

### Required Artifacts

Every task must produce:

```
SQL/Python: src/{pipeline}/
Configs: resources/{pipeline}.yml
Docs: docs/models/{pipeline}/
Quality: DQX YAML + Python apply script
Tests: Verification queries
```

### Git Workflow

Specification must include:

```
- Branch: {type}-{ticket-id}-{description}
- Commit: {type}({ticket-id}): {message}
- PR: Draft with checklist template
```

## Communication Patterns

### Keep User Informed

```
Status update points:
1_ After requirements gathering
2_ Before agent delegation
3_ During long-running tasks
4_ After review completion
5_ When blocked/clarification needed
```

### Present Findings

```markdown
## [Task Name] - [Status]

### What Was Done
[Brief summary]

### Key Findings
- Finding 1
- Finding 2

### Verification
- ✓ [Acceptance criterion 1]
- ✓ [Acceptance criterion 2]

### Next Steps
[If any]
```

## Stakeholder Questions Tool

### When to Ask

```
ambiguous_requirement → AskUserQuestion
multiple_valid_approaches → AskUserQuestion
trade-off_decision → AskUserQuestion
unclear_priority → AskUserQuestion
```

### Question Structure

```json
{
  "question": "Which approach should we use for [specific decision]?",
  "header": "Approach",
  "multiSelect": false,
  "options": [
    {
      "label": "Option 1",
      "description": "Trade-offs: [pros/cons]"
    },
    {
      "label": "Option 2",
      "description": "Trade-offs: [pros/cons]"
    }
  ]
}
```

## Escalation Strategy

### Escalate When

```
✗ Requirements too vague after 2 clarification rounds
✗ Technical blockers outside agent capabilities
✗ Conflicting requirements discovered
✗ Scope creep beyond original specification
```

### Escalation Format

```markdown
## Escalation Required: [Issue]

### Situation
[What's blocking]

### Attempts Made
1. [What was tried]
2. [Result]

### Options
1. [Option 1]: [Trade-offs]
2. [Option 2]: [Trade-offs]

### Recommendation
[If applicable]
```

## Self-Correction Mechanisms

### Validation Loop

```
1_ Define spec → 2_ User confirms
3_ Delegate → 4_ Review output
5_ ✓ Passes → Done | ✗ Fails → 6_ Provide feedback → 3_
```

### Quality Gates

```
Gate 1: Spec complete before delegation
Gate 2: Agent outputs match expected format
Gate 3: All acceptance criteria met before approval
Gate 4: Project standards verified
```

## Advanced Topics

See [orchestration-examples.md](orchestration-examples.md) for:
- Complex multi-agent workflows
- Error handling patterns
- MongoDB RAG integration
- Semantic search strategies

## Validation Workflow

### Execution Pattern

```
1_ Create specification from user request
2_ Validate spec completeness
3_ Get user approval
4_ Delegate to agents with context
5_ Monitor progress
6_ Review outputs against spec
7_ Provide feedback or approve
```

### Output Evidence

Gather for each task:

```
✓ Specification documented (markdown format)
✓ User confirmed requirements (AskUserQuestion result)
✓ Agent outputs collected (Task results)
✓ Acceptance criteria verified (checklist)
✓ Artifacts present (file paths)
✓ Standards verified (lint/test results)
```

### Success Criteria

```
✓ User understands what will be delivered
✓ All ambiguities resolved before work starts
✓ Agent outputs align with specification
✓ All acceptance criteria met
✓ Artifacts production-ready
✓ User confirms completion
```
