You are generating an implementation `plan.md` for a Linear issue. The SPEC has already been approved by a human operator. Your job is to break it down into shippable phases.

You have read access to this repository (Read, Glob, Grep tools). You may write exactly one file: `.symphony/plan.md`. Do not modify any other files. Do not run any commands.

## Issue

- **Identifier**: ${issue_identifier}
- **Title**: ${issue_title}
- **Status**: ${issue_state}
- **Priority**: ${issue_priority}
- **Labels**: ${issue_labels}
- **URL**: ${issue_url}

**Description**:

${issue_description}

## Approved SPEC

The following SPEC has been reviewed and approved. Do not deviate from it. Treat it as ground truth.

```markdown
${approved_spec_content}
```

## Your task

1. Read the relevant files in this repository to confirm the technical reality.
2. Write the plan to exactly `.symphony/plan.md` (relative to the working directory).
3. Do NOT modify any other files.
4. Do NOT run any commands.

## Required plan structure

The file you write MUST contain:

- A top-level `## Phases` header.
- 3-7 numbered phases beneath, each with this shape:

```
### Phase 1: <short name>

**Goal:** <one sentence>

- [ ] Concrete step naming a file path or function
- [ ] Concrete step naming a file path or function
- [ ] ...
```

- At least 3 unchecked checkbox items (`- [ ]`) total across all phases.
- Each phase must be shippable on its own in 1-2 hours of agent work.

## Style

- Be concrete. Each step references real files (paths you saw via Read/Glob).
- Do not invent files or APIs. If a step needs something that doesn't exist, write a step to create it explicitly.
- No prose between phases beyond the `**Goal:**` line.
- Concise: target 40-80 lines total.

When you finish, `.symphony/plan.md` must exist with `## Phases` and ≥3 `- [ ]` items.
