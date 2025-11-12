---
argument-hint: [branch_name] [ticket_class] [jira_ticket_number] [plan_file] [adw_id]
description: Create a pull request
---

# Create Pull Request

Based on the `Instructions` below, take the `Variables` follow the `Run` section to create a pull request. Then follow the `Report` section to report the results of your work.

## Variables

branch_name: $1
ticket_class: $2
jira_ticket_number: $3
plan_file: $4
adw_id: $5

## Instructions

- Generate a pull request title in the format: `<issue_type>(<jira_ticket_number>): <issue_title>`
- The PR body should include:
  - A summary section with the issue context
  - Link to the implementation plan file
  - Reference to the issue (Closes <jira_ticket_number>)
  - ADW tracking ID
  - A checklist of what was done
  - A summary of key changes made
- Examples of PR titles:
  - `feat(PROJ-123): Add user authentication`
  - `bug(PROJ-456): Fix login validation error`
  - `chore(PROJ-789): Update dependencies`

## Run

1. Run `git diff origin/main...HEAD --stat` to see a summary of changed files
2. Run `git log origin/main..HEAD --oneline` to see the commits that will be included
3. Run `git diff origin/main...HEAD --name-only` to get a list of changed files
4. Run `git push -u origin <branch_name>` to push the branch
5. Run `gh pr create --title "<pr_title>" --body "<pr_body>" --base main --label "ai"` to create the PR
6. Extract the PR URL from the output (it's typically the last line starting with <https://github.com/>)

## Report

Return ONLY the PR URL from the gh pr create output.
The URL will be on a line by itself, typically in the format: <https://github.com/owner/repo/pull/###>

Extract and return this URL with NO other text, explanations, or formatting.
