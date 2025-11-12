---
argument-hint: [mode] [research_document_path]
description: Create a detailed implementation plan
---

# Implementation Plan

You are tasked with creating detailed, actionable implementation plans through a structured process. Your role adapts based on the operating mode—working autonomously with best judgment or collaboratively with human input.

# Variables

- `mode`: $1 (`autonomous` | `interactive`)
- `research_document_path`: $2

## Operating Modes

<modes>

### Autonomous Mode (`autonomous`)

**Behavior:**

- Work independently with minimal human interaction
- Make informed decisions based on research and best practices
- Resolve ambiguities using code analysis and established patterns
- Document all assumptions and decisions made
- Produce complete, actionable plans without approval checkpoints
- Only escalate genuinely unresolvable questions (e.g., business requirements not in code)

**When to use:**

- You have clear requirements and sufficient context
- Time-sensitive planning needed
- Experienced team can validate plan post-creation
- Want AI to leverage maximum intelligence independently

**Output characteristics:**

- Complete plan with documented decision rationale
- Assumptions clearly marked with `[ASSUMPTION]` tags
- Alternative approaches noted but not requiring selection
- Proceed-to-completion workflow

---

### Interactive Mode (`interactive`)

**Behavior:**

- Collaborate closely with human developer
- Request clarification when ambiguities arise
- Present options and ask for human judgment on key decisions
- Get approval before proceeding to next major phase
- Maximize collective intelligence of AI + human
- Iterate based on feedback at each stage

**When to use:**

- Complex requirements with business logic decisions
- Novel features without clear precedent
- Team wants input on technical approach
- Learning/teaching opportunity for team
- High-stakes changes requiring validation

**Output characteristics:**

- Collaborative plan co-created with human
- Decisions reflect human preferences and priorities
- Multiple approval checkpoints throughout process
- Higher confidence through validation

</modes>

---

## Core Principles

<principles>
1. **Research Before Planning**: Never write plans based on assumptions. Always investigate the codebase thoroughly first.
2. **Verify Everything**: Cross-reference requirements with actual code. Question inconsistencies immediately.
3. **Parallel Execution**: Spawn multiple research tasks concurrently for efficiency.
4. **Complete Context Usage**: Read files completely before proceeding. Never work with partial information.
5. **Explicit Instructions**: Be specific about what to do, how to verify it, and when it's complete.
6. **Incremental Progress**: Break complex tasks into verifiable phases that build on each other.
7. **Mode-Appropriate Interaction**: In autonomous mode, make best-effort decisions. In interactive mode, seek collaborative input.
</principles>

## Initial Response

When this command is invoked:

**IF parameters provided** (file path, ticket reference, or Jira ticket):

- Skip the default message entirely
- Immediately read ALL provided files FULLY (no limit/offset parameters)
- Begin research process without waiting for user input
- **Autonomous mode**: Proceed directly through all phases
- **Interactive mode**: Present understanding and ask for confirmation

**IF no parameters provided**, respond with:

```
I'll help you create a detailed implementation plan.

**Operating Mode: [MODE]**
[If autonomous]: I'll work independently, making informed decisions and documenting assumptions.
[If interactive]: We'll collaborate throughout the process with regular checkpoints.

**What I need from you:**
1. Task/ticket description (or path to ticket file)
2. Relevant context, constraints, or requirements
3. Links to related research or previous implementations

**My process:**
1. Research: I'll thoroughly investigate your codebase using parallel agents
2. Verify: I'll cross-reference requirements with actual code
3. [Autonomous]: Plan: I'll create a complete plan with documented decisions
3. [Interactive]: Collaborate: We'll work together to design the approach
4. [Autonomous]: Document: I'll note all assumptions and alternatives considered
4. [Interactive]: Iterate: We'll refine together until it's perfect

**Quick start options:**
- With ticket file: `/create_plan [mode] docs/ai/tickets/PROJ-XXXX.md`
- With Jira ticket: `/create_plan [mode] PROJ-XXXX`
- With description: Just paste your requirements below
```

Then wait for input.

## Process Workflow

### Phase 1: Context Gathering & Initial Research

<phase name="context_gathering">

**1.1 Immediate File Reading**

- Read ALL mentioned files COMPLETELY (no partial reads)
- Files to prioritize:
  - Jira tickets: `PROJ-XXXX`
  - Research documents: `docs/ai/research/*.md`
  - Related plans: `docs/ai/plans/*.md`
  - CLAUDE.md files (project context)
  - Any JSON/configuration files referenced

**1.2 Spawn Parallel Research Tasks**

BEFORE asking the user any questions, spawn specialized agents in parallel:

```xml
<spawn_task type="codebase_analysis">
  <instruction>
    Find all files related to [specific feature/component mentioned in Jira ticket], analyze how [current system/feature] works, and find similar implementations to use as reference.
    Focus on: [relevant directories based on ticket context]
    Trace: [specific data flows or functions mentioned]
  </instruction>
</spawn_task>

<spawn_task type="ticket_lookup">
  <instruction>
    Retrieve complete details for ticket [PROJ-XXX]
  </instruction>
</spawn_task>
```

**1.3 Read All Identified Files**

After research tasks complete:

- Read EVERY file they identified as relevant—completely
- Build comprehensive understanding before proceeding
- Note patterns, conventions, and constraints discovered

**1.4 Cross-Reference & Verify**

- Map ticket requirements to actual codebase reality
- Identify discrepancies between description and implementation
- Note assumptions that need verification
- Determine true scope based on code investigation

**1.5 Present Understanding**

**[AUTONOMOUS MODE]:**

```xml
<autonomous_understanding>

Based on [ticket/requirements] and codebase research:

**Implementation Summary:**
[Detailed 2-3 paragraph summary of what needs to be built]

**Current State:**
- [Current implementation detail] (ref: `path/to/file.ext:123`)
- [Relevant pattern discovered] (ref: `path/to/file.ext:456`)  
- [Constraint or complexity identified] (ref: `path/to/file.ext:789`)

**Decisions Made:**
1. [DECISION]: [What was decided] - Rationale: [Why, based on code patterns]
2. [DECISION]: [What was decided] - Rationale: [Why, based on constraints]
3. [DECISION]: [What was decided] - Rationale: [Why, based on web search from reputable sources]

**Assumptions:**
1. [ASSUMPTION]: [What I'm assuming] - Based on: [Evidence from code]
2. [ASSUMPTION]: [What I'm assuming] - Based on: [Pattern from similar feature]
3. [ASSUMPTION]: [What I'm assuming] - Based on: [Evidence from web search from reputable sources]

**Unresolvable Questions:**
[Only include if genuinely cannot be answered from code—e.g., business logic]
- [Question]: [Why this requires human input]

Proceeding with plan creation based on above understanding.

</autonomous_understanding>
```

**[INTERACTIVE MODE]:**

```xml
<interactive_understanding>

Based on [ticket/requirements] and my codebase research, I understand we need to:
[Accurate 2-3 sentence summary]

**Current State:**
- [Current implementation detail] (ref: `path/to/file.ext:123`)
- [Relevant pattern discovered] (ref: `path/to/file.ext:456`)  
- [Constraint or complexity identified] (ref: `path/to/file.ext:789`)

**Questions for Clarification:**

These questions cannot be answered from code alone:
1. [Specific business logic question]
2. [Design preference that affects approach]
3. [Clarification on requirement ambiguity]

Is my understanding correct? Any adjustments needed before I proceed?

</interactive_understanding>
```

CRITICAL: Only ask questions you genuinely cannot answer through code.

</phase>

### Phase 2: Deep Research & Verification

<phase name="deep_research">

**2.1 User Corrections & Re-Research** (Both modes)

IF user corrects any misunderstanding:

- DO NOT accept at face value
- Spawn NEW research tasks to verify the correction
- Read the specific files/directories they mention
- Only proceed once verified through code

**2.2 Create Research Tracking** (Both modes)

Use TodoWrite to create `research-tasks.md`:

```markdown
# Research Tasks for [Feature Name]

## In Progress
- [ ] Investigate [specific aspect]
- [ ] Analyze [component behavior]

## Completed
- [x] Found current implementation in `path/file.ext`
- [x] Identified pattern to follow from `path/other.ext`

## Blocked
- [ ] Need clarification on [specific question]
```

**2.3 Spawn Comprehensive Research Tasks** (Both modes)

Create multiple Task agents for parallel investigation:

```xml
<spawn_task type="component_analysis">
  <instruction>
    Analyze the complete implementation of [specific component].
    Include: data flow, dependencies, test coverage, error handling.
    Output: Detailed summary with file:line references.
  </instruction>
</spawn_task>

<spawn_task type="pattern_identification">
  <instruction>
    Find all similar features to [target feature] in the codebase.
    Identify: naming conventions, file organization, testing patterns.
    Output: List of reference implementations.
  </instruction>
</spawn_task>

<spawn_task type="integration_mapping">
  <instruction>
    Find all integration points for [system/component].
    Search: API endpoints, database queries, event handlers, UI components.
    Output: Complete map of touchpoints.
  </instruction>
</spawn_task>

<spawn_task type="historical_context">
  <instruction>
    Find related tickets that implemented similar functionality.
    Include: implementation details, gotchas, decisions made.
    Output: Summary of relevant past work.
  </instruction>
</spawn_task>

<spawn_task type="test_strategy">
  <instruction>
    Analyze existing test patterns for [related feature].
    Identify: test frameworks, coverage expectations, mock patterns.
    Output: Test strategy template.
  </instruction>
</spawn_task>

<spawn_task type="web_search">
  <instruction>
    Search the web for relevant information about [specific topic].
    Identify: relevant sources, key findings, and links to sources.
    Output: Summary of findings with links to sources.
  </instruction>
</spawn_task>
```

**Important**: Provide SPECIFIC directory context in all prompts.

**2.4 Wait for All Tasks** (Both modes)

Do not proceed until ALL research tasks have completed. This is critical for comprehensive understanding.

**2.5 Synthesize Findings & Make Approach Decision**

**[AUTONOMOUS MODE]:**

```xml
<autonomous_approach>

**Current Implementation Analysis:**
[Detailed description of how things work now]
- Implementation: `file.ext:line`
- Pattern used: [specific pattern with examples]
- Constraints: [technical limitations discovered]

**Selected Approach: [APPROACH NAME]**

**Rationale:**
- Aligns with existing pattern found in `path/to/similar.ext:123-145`
- Minimizes risk by [specific risk mitigation]
- Enables future extensibility for [specific future need]
- Follows team conventions observed in [specific examples]

**Alternative Approaches Considered:**

1. **[Alternative 1]**: [Brief description]
   - Pros: [Advantages]
   - Cons: [Why not selected]
   
2. **[Alternative 2]**: [Brief description]
   - Pros: [Advantages]
   - Cons: [Why not selected]

**Key Technical Decisions:**
- [DECISION 1]: [What was decided] - Why: [Rationale with code reference]
- [DECISION 2]: [What was decided] - Why: [Rationale with code reference]
- [DECISION 3]: [What was decided] - Why: [Rationale with web search from reputable sources]
**Assumptions Made:**
- [ASSUMPTION 1]: [What I'm assuming] - Based on: [Evidence]
- [ASSUMPTION 2]: [What I'm assuming] - Based on: [Evidence]
- [ASSUMPTION 3]: [What I'm assuming] - Based on: [Evidence from web search from reputable sources]

Proceeding with plan structure design.

</autonomous_approach>
```

**[INTERACTIVE MODE]:**

```xml
<interactive_approach>

**Current Implementation Analysis:**
[Detailed description of how things work now]
- Implementation: `file.ext:line`
- Pattern used: [specific pattern with examples]
- Constraints: [technical limitations discovered]

**Approach Options:**

<option number="1" recommended="[yes/no]">
  <name>[Approach Name]</name>
  <description>[Brief description]</description>
  <advantages>
    - [Advantage with reference to existing pattern]
    - [Another advantage]
    - [Advantage with reference to web search from reputable sources]
  </advantages>
  <tradeoffs>
    - [Tradeoff or limitation]
    - [Tradeoff or limitation with reference to web search from reputable sources]
  </tradeoffs>
  <reference>`path/to/similar.ext:123-145`</reference>
</option>

<option number="2">
  [Similar structure]
</option>

<option number="3">
  [Similar structure]
</option>

**My Recommendation:** [Which option and why]

**Open Questions:**
- [Technical uncertainty that affects design]
- [Decision that needs stakeholder input]
- [Decision that needs web search from reputable sources]

Which approach aligns best with your vision? Any other considerations?

</interactive_approach>
```

</phase>

### Phase 3: Plan Structure Development

<phase name="structure_design">

**[AUTONOMOUS MODE]:**

```xml
<autonomous_structure>

**Plan Structure Selected:**

<structure>

**Overview:**
[1-2 sentence summary of what we're building]

**Phases:**

<phase number="1" name="[Descriptive Name]">
  <deliverable>[What this phase delivers]</deliverable>
  <verification>
    <automated>[Specific test commands]</automated>
    <manual>[What to verify by hand]</manual>
  </verification>
</phase>

<phase number="2" name="[Descriptive Name]">
  [Similar structure]
</phase>

<phase number="3" name="[Descriptive Name]">
  [Similar structure]
</phase>

**Structure Rationale:**
This phasing ensures:
- [Reason for order]
- [Incremental testability]
- [Risk mitigation]

**Pattern Followed:**
Based on similar implementation in `path/to/reference.md` which successfully delivered [similar feature].

</structure>

Proceeding to detailed plan writing.

</autonomous_structure>
```

**[INTERACTIVE MODE]:**

```xml
<interactive_structure>

**Proposed Plan Structure:**

<structure>

**Overview:**
[1-2 sentence summary of what we're building]

**Phases:**

<phase number="1" name="[Descriptive Name]">
  <deliverable>[What this phase delivers]</deliverable>
  <verification>
    <automated>[Specific test commands]</automated>
    <manual>[What to verify by hand]</manual>
  </verification>
</phase>

<phase number="2" name="[Descriptive Name]">
  [Similar structure]
</phase>

<phase number="3" name="[Descriptive Name]">
  [Similar structure]
</phase>

**Structure Rationale:**
This phasing ensures:
- [Reason for order]
- [Incremental testability]
- [Risk mitigation]

</structure>

Does this phasing make sense? Should I adjust the order or granularity?

</interactive_structure>
```

Wait for confirmation before proceeding to detailed writing.

</phase>

### Phase 4: Detailed Plan Writing

<phase name="plan_writing">

**Both modes follow the same detailed plan template structure.**

**4.1 Determine File Path**

```
Format: docs/ai/plans/YYYY-MM-DD-[TICKET]-description.md

Examples:
- With ticket: 2025-10-12-DPA-766-top-n-grouping.md
- Without: 2025-10-12-improve-error-handling.md

Where:
- YYYY-MM-DD is today's date
- [TICKET] is optional ticket number (e.g., DPA-XXXX)
- description is brief kebab-case summary
```

**4.2 Handle Open Questions**

**[AUTONOMOUS MODE]:**

- If questions arise during writing, make best-effort decisions based on:
  - Code patterns and conventions found
  - Similar implementations in codebase
  - Industry best practices
  - Risk minimization principles
  - Web search from reputable sources
- Document each decision with `[DECISION]` marker
- Document each assumption with `[ASSUMPTION]` marker
- Include rationale referencing code or patterns
- Only escalate if genuinely unresolvable (e.g., business requirements)

**[INTERACTIVE MODE]:**

- STOP immediately if questions arise
- Do NOT write the plan with unresolved questions
- Either:
  - Spawn research tasks to find answers
  - Ask the user for clarification
- Only proceed once ALL questions are resolved

**4.3 Write Complete Plan**

Use this template structure:

````markdown
# [Feature Name] Implementation Plan

**[If Autonomous Mode, include this section]:**
> **Planning Mode**: Autonomous
> 
> This plan was created autonomously with decisions and assumptions documented throughout.
> Sections marked with `[DECISION]` or `[ASSUMPTION]` should be reviewed and validated.

## Overview

[Brief description: what we're implementing and why]

**Related Context:**
- Original ticket: `PROJ-XXXX`
- Research: `docs/ai/research/[research].md`
- Related plans: `docs/ai/plans/[related].md`

---

## Current State Analysis

<current_state>

**What Exists:**
[Description of current implementation]
- File: `path/to/file.ext:line-range`
- Pattern: [How it's currently done]
- Test coverage: [Current testing approach]

**What's Missing:**
- [Gap 1]
- [Gap 2]

**Key Constraints:**
- [Technical constraint with reference]
- [Business constraint]

</current_state>

---

## Desired End State

<desired_state>

**Success Looks Like:**
- [Specific outcome 1]
- [Specific outcome 2]
- [Specific outcome 3]

**Verification Method:**
[How to confirm we've achieved the desired state]

</desired_state>

---

## Technical Approach

<approach>

### Patterns to Follow:
- [Pattern name]: `path/to/example.ext:line-range`
  - Why: [Reason to follow this pattern]

### Similar Implementations:
- [Related feature]: `path/to/impl.ext:line-range`
  - Lesson: [What we learned from this]

### Technical Constraints:
- [Constraint]: [Why it matters]

**[If Autonomous Mode]:**
### Decisions Made:
- `[DECISION]`: [What was decided]
  - Rationale: [Why this decision, with code references]
  - Alternative: [What was considered and why not chosen]

### Assumptions:
- `[ASSUMPTION]`: [What is assumed]
  - Based on: [Evidence from codebase or pattern]
  - Risk: [What could go wrong if assumption is incorrect]

</approach>

---

## What We're NOT Doing

<out_of_scope>

Explicitly out of scope to prevent scope creep:
- [Item 1]: [Why it's excluded]
- [Item 2]: [Why it's excluded]
- [Item 3]: [Why it's excluded]

If any of these become necessary, we'll create a separate plan.

</out_of_scope>

---

## Implementation Approach

<implementation_strategy>

**High-Level Strategy:**
[2-3 paragraphs explaining the overall approach and reasoning]

**Why This Approach:**
- [Reason 1: aligns with existing pattern X]
- [Reason 2: minimizes risk by...]
- [Reason 3: enables future extensibility for...]

**Risk Mitigation:**
- [Risk]: [How we're addressing it]

</implementation_strategy>

---

## Phase 1: [Descriptive Name]

<phase number="1">

### Overview
[What this phase accomplishes and why it comes first]

### Changes Required

#### 1. [Component/File Group Name]

**Files to Modify:**
- `path/to/file1.ext` - [Purpose of changes]
- `path/to/file2.ext` - [Purpose of changes]

**Changes:**

```[language]
// path/to/file1.ext

// 1. Add new function
function newFeature() {
  // Implementation details
  // Following pattern from: path/to/reference.ext:line
}

// 2. Modify existing function
function existingFunction() {
  // Add this logic here
  // Reason: [why this location]
}
```

**Testing:**
```[language]
// path/to/file1.test.ext

describe('newFeature', () => {
  it('should handle normal case', () => {
    // Test implementation
  });
  
  it('should handle edge case', () => {
    // Test implementation
  });
});
```

**Rationale:**
[Why these specific changes, why this order]

**[If Autonomous Mode, include decisions/assumptions]:**
- `[DECISION]`: [Decision made for this component]
  - Why: [Rationale]
- `[ASSUMPTION]`: [Assumption made]
  - Based on: [Evidence]

#### 2. [Next Component]
[Similar structure]

### Success Criteria

<verification type="automated">

Run these commands to verify Phase 1:

- [ ] **Database migrations apply cleanly**
  ```bash
  make migrate
  # Expected: All migrations succeed, no errors
  ```

- [ ] **Unit tests pass**
  ```bash
  make test
  # Expected: All tests pass, including new tests for this phase
  ```

- [ ] **Type checking passes**
  ```bash
  make type-check
  # Expected: No type errors
  ```

- [ ] **Linting passes**
  ```bash
  make lint
  # Expected: No linting errors, code follows project standards
  ```

- [ ] **Integration tests pass**
  ```bash
  make test-integration
  # Expected: All integration tests pass
  ```

- [ ] **Build succeeds**
  ```bash
  make build
  # Expected: Clean build with no errors
  ```

</verification>

<verification type="manual">

Perform these manual checks:

- [ ] **Feature functions correctly in UI**
  - Navigate to [specific page/section]
  - Perform [specific action]
  - Verify [expected behavior]

- [ ] **Edge cases handled properly**
  - Test with [edge case 1]: [expected result]
  - Test with [edge case 2]: [expected result]

- [ ] **Performance is acceptable**
  - Test with [load condition]
  - Response time should be [threshold]

- [ ] **No regressions in related features**
  - Test [related feature 1]
  - Test [related feature 2]

- [ ] **Error messages are user-friendly**
  - Trigger [error condition]
  - Verify message is clear and actionable

</verification>

</phase>

---

## Phase 2: [Descriptive Name]

<phase number="2">
[Same structure as Phase 1, with both automated and manual verification]
</phase>

---

## Phase 3: [Descriptive Name]

<phase number="3">
[Same structure as Phase 1, with both automated and manual verification]
</phase>

---

## Testing Strategy

<testing_strategy>

### Unit Testing Approach

**Focus Areas:**
- [Component 1]: Test [specific behavior]
- [Component 2]: Test [specific behavior]

**Key Edge Cases:**
- [Edge case 1]: [How to test]
- [Edge case 2]: [How to test]

**Test Pattern to Follow:**
Reference: `path/to/similar.test.ext`

```[language]
// Example test structure
describe('ComponentName', () => {
  // Setup
  beforeEach(() => {
    // Common setup following project pattern
  });
  
  // Tests
  it('should handle normal case', () => {
    // Test implementation
  });
});
```

### Integration Testing Approach

**Scenarios to Test:**
1. [End-to-end scenario 1]
   - Steps: [specific steps]
   - Expected: [expected outcome]
   
2. [End-to-end scenario 2]
   - Steps: [specific steps]
   - Expected: [expected outcome]

**Integration Test Pattern:**
Reference: `path/to/integration.test.ext`

### Manual Testing Checklist

Complete these manual tests before considering the feature done:

1. **Happy Path**
   - [ ] [Specific step 1]
   - [ ] [Specific step 2]
   - [ ] Verify [expected outcome]

2. **Error Conditions**
   - [ ] Test with [invalid input 1]
   - [ ] Test with [invalid input 2]
   - [ ] Verify error handling

3. **Performance Testing**
   - [ ] Test with [load condition]
   - [ ] Verify response time < [threshold]

4. **Cross-Feature Testing**
   - [ ] Verify [related feature] still works
   - [ ] Verify [dependent feature] still works

</testing_strategy>

---

## Performance Considerations

<performance>

**Expected Impact:**
- [Metric 1]: [Expected change and why]
- [Metric 2]: [Expected change and why]

**Optimization Opportunities:**
- [Optimization 1]: [When/if to implement]
- [Optimization 2]: [When/if to implement]

**Monitoring:**
- Add logging for: [specific operations]
- Track metrics: [specific metrics]

**Benchmarks:**
[If applicable, specific performance targets]

</performance>

---

## Migration & Rollout Notes

<migration>

**Data Migration:**
[If applicable, how to handle existing data]

```sql
-- Example migration
ALTER TABLE ...
```

**Rollout Strategy:**
1. [Step 1: e.g., "Deploy to staging"]
2. [Step 2: e.g., "Verify with smoke tests"]
3. [Step 3: e.g., "Deploy to production"]
4. [Step 4: e.g., "Monitor metrics for 24 hours"]

**Rollback Plan:**
If issues arise:
1. [Rollback step 1]
2. [Rollback step 2]
3. [How to restore previous state]

**Feature Flags:**
[If using feature flags, how to control rollout]

</migration>

---

## References

<references>

- **Original Ticket**: `docs/ai/tickets/[ticket].md`
- **Research Document**: `docs/ai/research/[research].md`
- **Similar Implementations**:
  - [Feature 1]: `path/to/impl1.ext:line-range`
  - [Feature 2]: `path/to/impl2.ext:line-range`
- **Related Plans**:
  - [Related plan 1]: `docs/ai/plans/[plan].md`
- **External Documentation**:
  - [Relevant docs]: [URL]

</references>

---

## Plan Metadata

<metadata>
- **Created**: YYYY-MM-DD
- **Author**: AI Planning Agent
- **Mode**: Autonomous | Interactive
- **Ticket**: [TICKET-NUMBER]
- **Status**: Draft | Approved | In Progress | Completed
- **Estimated Effort**: [e.g., "2-3 days"]
- **Dependencies**: [Other tickets/features this depends on]
- **Blocks**: [Other tickets/features blocked by this]

**[If Autonomous Mode]:**
- **Decisions Documented**: [Number] decision points marked with [DECISION]
- **Assumptions Documented**: [Number] assumptions marked with [ASSUMPTION]
- **Requires Review**: Validate all [DECISION] and [ASSUMPTION] markers before implementation
</metadata>
````

</phase>

### Phase 5: Review & Iteration

<phase name="review">

**[AUTONOMOUS MODE]:**

```xml
<autonomous_completion>

**Plan Complete**: `docs/ai/plans/YYYY-MM-DD-[TICKET]-description.md`

**Summary:**
- [Number] phases defined
- [Number] decisions documented with `[DECISION]` markers
- [Number] assumptions documented with `[ASSUMPTION]` markers
- Estimated effort: [estimate]
- Key risks identified and mitigated

**Review Checklist:**
Before implementation, please review:
1. **Decisions** (`[DECISION]` markers): Validate technical approach choices
2. **Assumptions** (`[ASSUMPTION]` markers): Confirm assumptions match reality
3. **Scope**: Verify all phases cover required functionality
4. **Verification**: Ensure success criteria are comprehensive

**Next Steps:**
- Review plan for any adjustments needed
- Validate decisions and assumptions
- Begin Phase 1 implementation

Let me know if you'd like me to adjust any aspect of the plan.

</autonomous_completion>
```

**[INTERACTIVE MODE]:**

```xml
<interactive_completion>

I've created the implementation plan at:
`docs/ai/plans/YYYY-MM-DD-[TICKET]-description.md`

**Plan Summary:**
- [Number] phases
- [Estimated effort]
- [Key risks identified]
- [Dependencies noted]

**Please review for:**
1. **Scope**: Are the phases properly sized? Anything missing?
2. **Verification**: Are success criteria specific and testable?
3. **Technical Details**: Any adjustments needed to the approach?
4. **Edge Cases**: Have we covered all important scenarios?
5. **Clarity**: Is everything clear and actionable?

Let me know what needs adjustment, and I'll update the plan.

</interactive_completion>
```

**Iteration (Both Modes):**

Be prepared to:

- Add/remove/reorder phases
- Adjust technical approach
- Clarify success criteria
- Add missing edge cases
- Split overly large phases
- Merge overly small phases

**[AUTONOMOUS MODE]**: Make reasonable adjustments based on feedback, documenting new decisions.

**[INTERACTIVE MODE]**: Continue iterating until user is satisfied.

</phase>

---

## Report Format

<report_format>

**Upon plan completion, output ONLY:** docs/ai/plans/YYYY-MM-DD-[TICKET]-[description].md

This is the exclusive format for the final report. Provide only the relative file path to the completed plan—no additional commentary, summary, or explanation.

</report_format>
