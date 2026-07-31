---
name: provide-info
description: Use when the user wants information, an explanation, or an answer about the codebase or system, with NO code changes — a read-only question. Triggers on "explain", "how does X work", "where is", "what does", "why does", "giải thích", "cho tôi biết", "tra cứu", "tìm hiểu", research and Q&A requests.
---

# Provide Info — read-only

## Overview
Answer the user's question by reading and explaining. **Make no changes** — the
deliverable is information, not a modification.

## Core rule
**Read-only. Do not write.** No Edit, Write, or NotebookEdit; no new files; no
commits; no state-changing or destructive commands (install, migrate, generate,
delete, format-in-place). Use only reading/inspection: read files, search/grep,
`git log/show/diff`, and read-only inspection. Run a build or test ONLY if it is
necessary to answer the question and it does not mutate the user's working tree
or data.

## Process
1. **Gather** — read the relevant files; search broadly; follow references. Delegate wide searches to a read-only Explore agent when it saves context.
2. **Verify** — confirm against the actual code. Do not answer from memory or assumption; open the file and check.
3. **Answer** — lead with the direct answer, then the supporting detail with concrete `file:line` references.
4. **Offer, don't act** — if a fix or change is the natural next step, DESCRIBE it and offer to do it. Do not make the change in this mode.

## Output shape
- **Direct answer** first — the one-paragraph bottom line.
- **Evidence** — `file:line` references, the relevant flow, short snippets where they clarify.
- **Caveats / unknowns** — anything you couldn't confirm.
- Optional: *"Want me to change this?"* — strictly as an offer, never as an action taken.

## Red flags — STOP
- Reaching for Edit / Write / commit → not allowed in this mode; offer instead.
- "I'll just fix this small thing while I'm here" → no. Describe it, ask.
- Answering from memory without opening the file → read first, then answer.
- Running a command that changes state (install, migrate, write, delete) → don't.
