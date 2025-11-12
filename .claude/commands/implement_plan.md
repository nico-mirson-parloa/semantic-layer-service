---
argument-hint: [mode] [plan_path]
description: Implement a technical plan
---

# Implement Plan

You are tasked with implementing an approved technical plan. These plans contain phases with specific changes and success criteria.

## Variables

- `mode`: $1 (`autonomous` | `interactive`)
- `plan_path`: $2

## Context Awareness

Your context window will be automatically compacted as it approaches its limit, allowing you to continue working indefinitely from where you left off. Therefore, do not stop tasks early due to token budget concerns. Focus on making steady progress on a few things at a time rather than attempting everything at once.

## Operating Modes

### Autonomous Mode

Work independently to implement the plan with minimal human intervention:

- **Make technical decisions**: Use your judgment to resolve ambiguities. Document your reasoning explicitly.
- **Research when needed**: Use web_search to find solutions, best practices, API documentation, or similar implementations.
- **State assumptions clearly**: When making assumptions, document them: "Assumption: X because Y."
- **Maintain forward momentum**: The goal is progress. Don't wait when you can research or make informed decisions.
- **Handle mismatches proactively**: Analyze, choose the best path forward, and document your decision.
- **Execute in parallel**: Run multiple bash commands simultaneously when possible to maximize efficiency.

Example autonomous decision:

```
<decision>
Issue: Plan expects DatabaseService in src/services/ but found db/ directory instead.
Analysis: Codebase uses db/ for all database code. Found similar patterns in UserRepository and OrderRepository.
Decision: Implementing in db/services/DatabaseService.ts to match existing conventions.
Reasoning: Consistency with established codebase patterns is more important than the plan's initial assumption.
</decision>
```

### Interactive Mode

Collaborate closely with the human developer:

- **Seek clarification early**: Ask questions when requirements are ambiguous before implementing.
- **Present options with analysis**: Show multiple approaches with pros/cons, then ask for input.
- **Get approval for architectural choices**: Request feedback before making significant decisions.
- **Discuss blockers**: When facing mismatches or issues, present the situation clearly and wait for guidance.
- **Verify understanding**: Confirm interpretation of requirements before proceeding with implementation.

Example interactive question:

```
I found a mismatch in Phase 2:

Expected: DatabaseService in src/services/
Found: Existing db/ directory with UserRepository and OrderRepository

Options:
1. Create src/services/DatabaseService.ts (follows plan exactly, but inconsistent with codebase)
2. Create db/services/DatabaseService.ts (consistent with existing structure)
3. Refactor entire db/ directory to src/services/ (comprehensive but time-consuming)

Recommendation: Option 2 for consistency with existing patterns.

How should I proceed?
```

## Getting Started

<instructions>
When given a plan path, follow these steps:

1. **Understand the starting state**:
   - Call `pwd` to confirm your working directory
   - Run `git status` and `git log --oneline -10` to see recent changes
   - Check for existing checkmarks (- [x]) in the plan to identify completed work

2. **Read the plan completely**:
   - Review "Desired End State" and overall goals
   - Check "Current State Analysis" and "Implementation Approach"
   - Note all phases and their success criteria
   - **Read files fully** - NEVER use limit/offset parameters

3. **Gather context**:
   - **JIRA TICKETS**: If plan references ticket files (e.g., docs/ai/tickets/PROJ-123.md), read them directly. If plan references raw ticket IDs (e.g., PROJ-123), spawn **jira-ticket-reader** agent
   - Read research documents from the plan's References section
   - Read all files mentioned in the plan
   - Review CLAUDE.md if it exists for project-specific conventions

4. **Create execution plan**:
   - Use TodoWrite to track phases and major subtasks
   - Mark phases as in_progress/completed as you work
   - Keep todos aligned with plan phases

5. **Begin implementation**:
   - **Autonomous**: Start Phase 1 once you understand requirements. Research or make documented assumptions if unclear.
   - **Interactive**: Confirm understanding, then start Phase 1. Ask questions if anything is unclear.

**If no plan path provided**, ask the user for one.
</instructions>

## Implementation Philosophy

<philosophy>
Plans are carefully designed, but reality is messy. Your job:

- Follow the plan's **intent** while adapting to reality
- Implement each phase **completely** before moving to next
- Verify work makes sense in the broader codebase context
- Update checkboxes in the plan as you complete items (use Edit/SearchReplace tool)
- Make steady progress on a few things at a time
- Maintain orientation across extended sessions

When the codebase doesn't match expectations:

- **Autonomous**: Analyze, research similar patterns, choose best path, document decision
- **Interactive**: Present issue clearly with options and wait for guidance
</philosophy>

## Handling Mismatches

### Autonomous Mode Response

```
<adaptation>
Phase: [N] - [Phase Name]
Expected: [plan expectation]
Found: [actual situation]
Research: [similar patterns found in codebase or online]
Decision: [chosen approach]
Reasoning: [why this makes sense]
Assumptions: [any assumptions made]
</adaptation>
```

### Interactive Mode Response

```
<issue>
Phase: [N] - [Phase Name]
Expected: [plan expectation]
Found: [actual situation]
Impact: [why this matters]

Options:
1. [Approach with pros/cons]
2. [Alternative with pros/cons]
3. [Another option if relevant]

Recommendation: [your suggested approach with brief reasoning]

How should I proceed?
</issue>
```

## Verification Strategy

<verification>
Each phase has **Success Criteria** divided into:

### Automated Verification

Commands you can run directly:

- `make tests` - Run all tests
- `make lint` - Check formatting and linting
- `make type-check` - Run type checking
- Other project-specific commands from the plan

**When to run**: After completing each phase, before moving to next.

### Manual Verification

Items requiring human testing:

- UI/UX functionality
- Performance under real conditions
- Edge cases difficult to automate
- End-to-end workflows

**Note these for the user to verify.**

### Execution Approach

- Batch verification at natural stopping points
- Run automated checks after each phase
- Fix issues immediately before proceeding
- Update checkboxes in plan file (Edit/SearchReplace)
- Update todo list to stay in sync
- **Autonomous**: Debug and fix test failures independently
- **Interactive**: Present test failures with findings if unclear

### Parallel Execution

Execute multiple bash commands simultaneously when safe to do so. For example:

```bash
make lint & make type-check & make test-unit
```

</verification>

## Using Sub-Agents

<sub_agents>
**Available agents** (in `.claude/agents/`):

- **jira-ticket-reader** - Read JIRA ticket details
- **codebase-analyzer** - Find where code lives, understand how it works, and discover existing patterns
- **web-search-researcher** - Find external documentation and resources.

**When to use**:

- Need to understand unfamiliar codebase parts
- Debugging complex issues
- Need to find similar patterns to follow
- Plan references unfamiliar code
- Need to find external documentation and resources

**Mode-specific usage**:

- **Autonomous**: Use proactively to gather information for decisions
- **Interactive**: Use to prepare context before asking human for decisions

**How to use**:

- Spawn sub-tasks with specific, focused questions
- Wait for results before proceeding
- Use findings to inform implementation

Use sub-tasks sparingly - mainly for targeted debugging or exploration.
</sub_agents>

## File Management

<file_management>

- **Reading files**: Always read completely (no limit/offset parameters)
- **Temporary files**: If you create temporary files for testing/iteration, clean them up at task end
- **Checkboxes**: Update plan checkboxes as you complete items
- **Code quality**: Follow existing patterns and conventions

Example cleanup instruction in your working notes:

```
Created temporary files:
- scripts/test_migration.py (for testing)
- tmp_output.json (validation data)

TODO: Remove before completing phase
```

</file_management>

## Resuming Work

<resuming>
If plan has existing checkmarks (- [x]):
- **Trust completed work is done**
- Pick up from first unchecked item
- Verify previous work only if tests fail or something seems off
- Update todo list to reflect completed items
- Review git logs to understand recent changes
</resuming>

## Report Format

<report_format>
At the end of your implementation, provide a report in this exact format:

**Summary**: [10-50 words describing what changed]

**Changes**:

```
[Output of: git diff --stat]
```

Example:
**Summary**: Implemented database connection pooling with retry logic and added comprehensive error handling for connection failures.

**Changes**:

```
 src/db/connection.ts        | 45 +++++++++++++++++++++++++----
 src/db/pool.ts             | 89 +++++++++++++++++++++++++++++++++++++++++++++++++++
 tests/db/connection.test.ts | 67 ++++++++++++++++++++++++++++++++++++++
 3 files changed, 195 insertions(+), 6 deletions(-)
```

Keep the summary concise and focused on the most important changes. The git diff --stat provides the detailed file-level view.
</report_format>

## Important Reminders

<reminders>
- **Use XML tags** for structured sections in your responses (like `<decision>`, `<issue>`, `<adaptation>`)
- **Be explicit** about which tools you're using and why
- **Forward momentum**: Keep end goal in mind; implement solutions, not just checkboxes
- **Stay in mode**: Maintain operating mode (autonomous/interactive) consistently
- **Document decisions**: In autonomous mode, always document reasoning and assumptions
- **Communicate clearly**: In interactive mode, provide context for informed decision-making
- **Parallel execution**: Run multiple commands simultaneously when appropriate
- **Context efficiency**: Make steady progress on a few things at a time
- **Clean up**: Remove temporary files created during implementation
- **Use Makefile commands**: Leverage project-specific make targets for verification
</reminders>

Remember: You're implementing a solution that solves a real problem. Maintain forward momentum while respecting your operating mode and the quality standards of the codebase.
