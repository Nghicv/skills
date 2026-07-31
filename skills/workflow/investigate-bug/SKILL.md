---
name: investigate-bug
description: Use when the user wants a bug investigated down to an accurate, evidence-backed root cause with a proposed fix, but wants to review and approve before any code is changed. Triggers on "investigate", "find the root cause", "tìm nguyên nhân", "điều tra bug", "don't fix yet", "propose a fix first", "đừng sửa vội".
---

# Investigate Bug — propose, don't implement

## Overview
Investigate to a PROVEN root cause and propose a fix — then **STOP and wait** for
the user's explicit go-ahead before changing any production code. The deliverable
is a diagnosis plus a plan, not a patch.

**REQUIRED SUB-SKILL:** Use **superpowers:systematic-debugging** for the
investigation itself.

## Core rule
**Do not modify production code until the user explicitly confirms the proposed
fix.** Investigation is read + diagnose only. Editing the fix — even "just to
prove it works" — comes AFTER confirmation, not before.

The only writes allowed during investigation are temporary, reversible
diagnostics (log lines, a throwaway reproduction script). Revert them before you
hand off.

## Process
1. Reproduce and trace using systematic-debugging — read code, follow the failing path, add temporary logging if needed.
2. **Prove** the root cause. Do not stop at the symptom or a plausible-sounding guess. State the evidence that pins it down.
3. Design the fix: the concrete change, the file(s)/line(s), the right level to fix it at, and the trade-offs.
4. Present the findings and STOP. End by asking the user to confirm before you implement.

## Required output shape
- **Root cause** — the actual mechanism, with evidence (`file:line`, the failing path).
- **Why it happens** — the chain from cause to observed symptom.
- **Proposed fix** — concrete change(s), where, and why this is the correct level (not a band-aid).
- **Risks / alternatives** — blast radius, edge cases, and any option B worth considering.
- **Confidence** — high / medium / low, plus what would raise it.
- Final line: **"Confirm and I'll implement."** Then stop — do not implement.

## Rationalizations — all of these mean STOP and wait
| Excuse | Reality |
|---|---|
| "The fix is tiny, I'll just apply it" | Size is irrelevant; the user asked to confirm first. Propose, wait. |
| "Implementing it is how I prove the root cause" | Present evidence instead. Confirmation gates the edit. |
| "They'll obviously want this fix" | Then it costs them one word to confirm. Ask. |
| "I'm already in the right files" | Proximity is not permission. Stop at the diagnosis. |
| "I'll write it and just not commit" | Editing the working tree is still changing code. Don't. |

## Red flags
- Reaching for Edit/Write on production code before the user has replied → STOP.
- Presenting a guess as "the root cause" without evidence → keep digging.
- Skipping the explicit "Confirm and I'll implement." gate.
