You are generating a SPEC.md document for a Linear issue. The SPEC will be reviewed by a human operator before any code is written.

You have read access to this repository (Read, Glob, Grep tools) and write access to exactly one path. Do not modify any other files. Do not run any commands.

## Issue

- **Identifier**: ${issue_identifier}
- **Title**: ${issue_title}
- **Status**: ${issue_state}
- **Priority**: ${issue_priority}
- **Labels**: ${issue_labels}
- **URL**: ${issue_url}

**Description**:

${issue_description}

## Your task

1. Read the relevant files in this repository to understand the existing patterns. Look at 1-2 similar features before writing.
2. Write a SPEC.md file at exactly `.symphony/spec.md` (relative to the working directory).
3. Do NOT modify any other files.
4. Do NOT run any commands (no Bash, no shells).

## Required SPEC structure

The file you write MUST contain the following Markdown headers, in any order, with non-empty content beneath each:

- `## Goals` — what success looks like; 3-5 concrete bullet points
- `## Non-Goals` — what is intentionally out of scope; 2-3 bullet points
- `## Constraints` — technical limits, security boundaries, perf budgets, compatibility requirements
- `## Approach` — narrative overview of how the change should be made; reference specific files and existing patterns

## Style

- Be concrete. Reference real file paths and existing patterns you saw in the repo.
- Do NOT invent files, APIs, or libraries that do not exist in this repo.
- Concise: target 30-60 lines total in the SPEC.
- Markdown body only — no code execution, no YAML front matter.

When you finish, the file `.symphony/spec.md` must exist with the four required sections. The orchestrator will read it from there.
