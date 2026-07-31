---
name: quick-fix
description: Use when the user wants a fast, lean fix for a small or well-understood bug/change and wants to skip TDD, parallel subagents, and heavy multi-phase planning. Triggers on "quick fix", "fix nhanh", "sửa nhanh", "just fix it", "small fix skip TDD", "fix gọn".
---

# Quick Fix

## Overview
A fast lane for small, well-understood fixes. Cut the ceremony — no test-first
TDD cycle, no fan-out of subagents, no multi-phase plan. But speed comes from
removing ceremony, NOT from removing correctness: you still confirm the cause
before editing and still verify the fix actually works.

## When to use
- Small, localized bug or change with a clear, obvious cause
- The user explicitly asked for a quick fix / "fix nhanh" / "skip TDD"
- Low blast radius — one or a few files, no architectural or contract change

## When NOT to use — escalate instead
- Root cause is unclear or you'd be guessing → use **investigate-bug** or
  **superpowers:systematic-debugging**
- Security / auth / payments / data-migration code → do not shortcut; do it properly
- Change spreads across many modules or touches public/shared contracts → use the
  full plan + TDD flow
- The "fix" keeps growing as you work → stop and plan it properly

## The flow (do these in order)
1. **Locate** — read the relevant code directly. Confirm the *actual* cause. Do not guess.
2. **Fix** — make the minimal, correct change. Match the surrounding style. No drive-by refactors or unrelated cleanups.
3. **Verify** — build and/or run the narrowest relevant test or the real app path, and look at the output. A fix you did not verify is not done.
4. **Report** — one tight summary: what was wrong, what you changed (`file:line`), how you verified it.

## Skip vs keep
| Skip (ceremony) | Keep (correctness) |
|---|---|
| Writing a failing test first | Reading the code before you edit it |
| Spawning subagents / parallel fan-out | A minimal, focused diff |
| Multi-phase written plans | Real verification with actual output |
| Surveying every possible option | Honest reporting of what you did |

## Red flags — STOP and escalate
- "I'll just guess and let the user correct me" → confirm the cause first.
- Cause still unclear after a look → switch to **investigate-bug**.
- The diff is sprawling across many files → stop, plan it properly.
- "It's obvious, I'll skip the build/test" → verify anyway; obvious fixes break too.
