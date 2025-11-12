---
argument-hint: [jira-ticket-file-path]
description: Classify a Jira ticket from a cached file
---

# Classify Jira Ticket

Read the Jira ticket from the provided file path, then classify it into exactly ONE category.

## Categories

- `feat` - New features or enhancements
- `fix` - Bug fixes or error corrections
- `chore` - Maintenance, refactoring, dependency updates, CI/CD
- `docs` - Documentation changes only
- `0` - Does not fit any category above

## Examples

feat - "Add OAuth2 authentication support"
feat - "Implement user profile dashboard"
fix - "Fix login button crash on mobile"
fix - "Resolve memory leak in data processor"
chore - "Update React to v18"
chore - "Refactor authentication module"
docs - "Add API documentation for user endpoints"
0 - "Schedule team meeting"

## Critical Output Requirement

**RESPOND WITH ONLY THE CATEGORY WORD. NO EXPLANATION. NO FORMATTING.**

Valid outputs: `feat` `fix` `chore` `docs` `0`

## Jira Ticket File Path

$ARGUMENTS
