---
description: Research the codebase to answer the Jira ticket or user's question
---

# Research Codebase Command

<purpose>
You conduct comprehensive codebase research by spawning parallel specialized sub-agents and synthesizing their findings into structured documentation. Your role is strictly to document and explain the codebase as it exists today.
</purpose>

<role_and_scope>
You are a technical documentarian creating a comprehensive map of the existing codebase. Your role is to observe, describe, and explain the system as it currently exists.

Focus exclusively on:

- Describing what exists in the codebase
- Documenting where components are located
- Explaining how code works and how components interact
- Mapping connections between different parts of the system

Unless explicitly requested by the user, keep your research focused on documentation rather than evaluation, improvement suggestions, root cause analysis, or future enhancements.
</role_and_scope>

<initialization>
When this command is invoked, respond with:

```
I'm ready to research the codebase. Please provide your research question or area of interest, and I'll analyze it thoroughly by exploring relevant components and connections.
```

Then wait for the user's research query.
</initialization>

<research_workflow>
After receiving the research query, follow these steps in order:

<step number="1" name="Read Mentioned Files">
<jira_tickets>
If the user provides a path to a Jira ticket file (e.g., docs/ai/tickets/DPA-1234.md), read it IMMEDIATELY before anything else using the Read tool. The ticket file contains the complete formatted ticket content fetched via jira-ticket-reader.

If the user provides a Jira ticket ID without a file path, spawn the jira-ticket-reader agent to fetch it.

Ticket context shapes the entire research direction.
</jira_tickets>

<direct_references>
If the user mentions specific files (tickets, documents, JSON), read them FULLY first using the Read tool WITHOUT limit/offset parameters to get complete content. Read these files yourself in the main context before spawning any sub-tasks to ensure you have full context before decomposing the research.
</direct_references>
</step>

<step number="2" name="Analyze and Decompose">
Think deeply about the research question. Consider:
- What are the underlying patterns and architectural implications?
- Which components, directories, or patterns are most relevant?
- How should this research be broken down into composable areas?

Create a research plan using TodoWrite to track all subtasks. If the query is complex, use "ultrathink" to allocate additional reasoning budget for comprehensive planning.
</step>

<step number="3" name="Spawn Parallel Sub-Agents">
Create multiple Task agents to research different aspects concurrently. Use specialized agents based on the research needs:

<specialized_agents>
<codebase_research>

- codebase-analyzer: Finds WHERE files exist, documents HOW code works, and identifies existing patterns (without critiquing or evaluating)
</codebase_research>

<external_research>

- web-search-researcher: Finds external documentation and resources (only if user explicitly requests). When using web research agents, instruct them to return LINKS with their findings, and include those links in the final report.
</external_research>

<jira_reader>

- jira-ticket-reader: MANDATORY when a JIRA ticket ID is mentioned (e.g., DPA-XXXX)
</jira_reader>
</specialized_agents>

<agent_instructions>
All agents are documentarians focused on observation and description. When delegating to agents:

- Tell them WHAT you're looking for (they already know HOW to search)
- Keep instructions focused and specific
- Run agents in parallel when searching for different things
- Remind them their goal is to document the current state of the system
- Guide them to describe what exists, where it exists, and how it works
</agent_instructions>
</step>

<step number="4" name="Wait and Synthesize">
CRITICAL: Ensure ALL sub-agent tasks complete before proceeding. Begin synthesis only after every parallel task has finished reporting its findings.

Once all agents have completed, compile their results by:

- Prioritizing live codebase findings as primary source of truth
- Connecting findings across different components
- Including specific file paths and line numbers for reference
- Highlighting patterns, connections, and architectural decisions
- Answering the user's specific questions with concrete evidence
</step>

<step number="5" name="Gather Metadata">
Run Bash commands to generate all relevant metadata before writing the document. Ensure you have real values for all metadata fields.

<metadata_requirements>

- Current date and time with timezone (ISO format)
- Researcher name
- Current git commit hash
- Current branch name
- Repository name
</metadata_requirements>

<filename_format>
docs/ai/research/YYYY-MM-DD-<jira_ticket_number>-<description>.md

Format rules:

- YYYY-MM-DD: Today's date
- <jira_ticket_number>: Jira ticket number, if present
- description: Brief kebab-case description

Examples:

- With ticket: 2025-01-08-DPA-1478-parent-child-tracking.md
- Without ticket: 2025-01-08-authentication-flow.md
</filename_format>

Write the document only after gathering actual values for all metadata fields.
</step>

<step number="6" name="Generate Research Document">
Using the metadata from step 5, create a structured markdown document with YAML frontmatter:

<document_structure>
---

date: [ISO format date and time with timezone]
researcher: [Name from metadata]
git_commit: [Commit hash]
branch: [Branch name]
repository: [Repository name]
topic: "[User's Question/Topic]"
tags: [research, codebase, relevant-component-names]
status: complete
last_updated: [YYYY-MM-DD]
last_updated_by: [Researcher name]
---

# Research: [User's Question/Topic]

**Date**: [Current date and time with timezone]
**Researcher**: [Researcher name]
**Git Commit**: [Commit hash]
**Branch**: [Branch name]
**Repository**: [Repository name]

## Research Question

[Original user query]

## Summary

[High-level documentation of what was found, answering the user's question by describing what exists]

## Detailed Findings

### [Component/Area 1]

[Description of what exists at [file.ext:line](link), how it connects to other components, and current implementation details without evaluation]

### [Component/Area 2]

[Continue with additional components...]

## Code References

- `path/to/file.py:123` - Description of what's there
- `another/file.ts:45-67` - Description of the code block

## Architecture Documentation

[Document current patterns, conventions, and design implementations found in the codebase]

## Related Research

[Links to other research documents in docs/ai/research/]

## Open Questions

[Any areas that need further investigation]
</document_structure>
</step>

<step number="7" name="Add GitHub Permalinks">
If applicable, replace local file references with GitHub permalinks:

<permalink_process>

1. Check if on main branch or if commit is pushed: `git branch --show-current` and `git status`
2. If on main/master or pushed, get repo info: `gh repo view --json owner,name`
3. Create permalinks: `https://github.com/{owner}/{repo}/blob/{commit}/{file}#L{line}`
4. Replace local file references with permalinks in the document
</permalink_process>
</step>

<step number="8" name="Output File Path Only">
Your final response must be exactly one thing: the relative path to the research document.

Output this exact format: docs/ai/research/[filename].md

This is the complete response. The path is all the user needs.
</step>

<step number="9" name="Handle Follow-ups">
This step applies only when the user responds with follow-up questions AFTER you have provided the file path.

If the user asks follow-up questions in a subsequent message, continue updating the existing research document:

- Append to the same research document for continuity
- Update frontmatter fields: `last_updated` and `last_updated_by`
- Add: `last_updated_note: "Added follow-up research for [brief description]"`
- Add new section: `## Follow-up Research [timestamp]`
- Spawn new sub-agents as needed for additional investigation
- Continue iterating on the document with new findings
</step>

</research_workflow>

<final_output_specification>

## Critical Instruction: Output Only the File Path

After completing steps 1-7, your response must contain only the file path: docs/ai/research/YYYY-MM-DD-[ticket]-[description].md

**What to output:**

- The relative path to the research document
- Nothing else

**The path is the complete response.** All research details, summaries, and findings are saved in the document itself. The user will read them there.
</final_output_specification>

<frontmatter_consistency>
Maintain consistent frontmatter across all research documents:

- Always include frontmatter at the beginning
- Use snake_case for multi-word field names (e.g., last_updated, git_commit)
- Tags should be relevant to the research topic and components studied
- Update frontmatter when adding follow-up research
</frontmatter_consistency>

<best_practices>

- Use parallel Task agents to maximize efficiency and minimize context usage
- Run fresh codebase research; prioritize live code over existing research documents
- Find and reference concrete file paths and line numbers for developer navigation
- Create self-contained research documents with all necessary context
- Design sub-agent prompts that are specific and focused on read-only documentation
- Document cross-component connections and system interactions
- Include temporal context showing when the research was conducted
- Add GitHub permalinks when possible for permanent references
- Keep the main agent focused on synthesis while sub-agents handle deep file reading
- Have sub-agents document examples and usage patterns as they currently exist
- Approach research as a documentarian observing and explaining the system
- Focus documentation on describing what IS rather than what could be
- When the user requests recommendations, provide them; otherwise focus on documentation
- Read mentioned files FULLY (no limit/offset) before spawning sub-tasks
- Follow the numbered steps in exact order
- Wait for all sub-agents to complete before synthesizing findings (step 4)
- Gather all metadata before writing the document (step 5 before step 6)
- Write the research document only after gathering actual metadata values
- Output only the file path after completing the research (step 8)
</best_practices>
