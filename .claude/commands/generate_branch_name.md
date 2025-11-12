---
argument-hint: [jira_ticket_class] [adw_id] [jira_ticket_number]
description: Generate a Git branch name
---

# Generate Git Branch Name

Based on the `Instructions` below, take the `Variables` follow the `Run` section to generate a concise Git branch name following the specified format. Then follow the `Report` section to report the results of your work.

## Variables

jira_ticket_class: $1
adw_id: $2
jira_ticket_number: $3

## Instructions

- Generate a branch name in the format: `<jira_ticket_class>-<jira_ticket_number>-<adw_id>-<concise_name>`
- The `<concise_name>` should be:
  - 3-6 words maximum
  - All lowercase
  - Words separated by hyphens
  - Descriptive of the main task/feature
  - No special characters except hyphens
- Examples:
  - `feat-PROJ-123-a1b2c3d4-add-user-auth`
  - `bug-PROJ-456-e5f6g7h8-fix-login-error`
  - `chore-PROJ-789-i9j0k1l2-update-dependencies`
- If $3 is a file path (contains "/"), read the ticket from that file
- Otherwise, use jira-ticket-reader agent to fetch ticket $3

## Run

Run `git checkout main` to switch to the main branch
Run `git pull` to pull the latest changes from the main branch
Run `git checkout -b <branch_name>` to create and switch to the new branch

## Report

After generating the branch name:
Return ONLY the branch name that was created (no other text)
