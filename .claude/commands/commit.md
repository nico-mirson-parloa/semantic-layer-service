---
argument-hint: [agent_name] [jira_ticket_number] [files]
description: Generate a Git commit
---

# Generate Git Commit

Based on the `Instructions` below, take the `Variables` follow the `Run` section to create a git commit with a properly formatted message. Then follow the `Report` section to report the results of your work.

## Variables

agent_name: $1
jira_ticket_number: $2
files: $3

## Instructions

- Generate the following elements for the commit message:
  - `changes_class`: `feat`, `fix`, `chore`, `docs`.
  - `changes_description`: A brief description of the changes made.
- Generate a concise commit message in the format: `<changes:class>(<jira_ticket_number>): <agent_name>: <commit message>`
- The `<commit message>` should be:
  - Present tense (e.g., "add", "fix", "update", not "added", "fixed", "updated")
  - 50 characters or less
  - Descriptive of the actual changes made
  - No period at the end
- Examples:
  - `docs(PROJ-123): adw_codebase_researcher: Add research document for feature implementation`
  - `fix(PROJ-123): adw_builder: Fix permissions issue`
  - `feat(PROJ-123): adw_builder: Add improved authentication`
  - `chore(PROJ-123): adw_builder: Update dependencies`
- Make sure to include the `jira_ticket_number` in the commit message.

## Run

1. IF `files` is present, run `git add <files>` to stage the changes
2. ELSE, run `git add -A` to stage all changes
3. Run `git diff HEAD` to understand what changes have been made
4. Run `git commit -m "<generated_commit_message>"` to create the commit
5. Push the commit to the remote repository

## Report

Return ONLY the commit message that was used (no other text)
