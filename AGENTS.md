# Agent instructions for this repo

This repo is the single source of truth for the owner's personal Agent Skills,
consumed by both Claude Code (`~/.claude/skills`) and Codex / other
Agent-Skills-compatible harnesses (`~/.agents/skills`) via symlinks created by
`scripts/install.sh`.

## Layout rules

- Every skill lives at `skills/<domain>/<skill-name>/SKILL.md`. Domains:
  `android`, `ios`, `mobile` (cross-platform), `backend`, `frontend`,
  `workflow` (process skills like quick-fix, investigate-bug), `tools`.
- Exactly this depth — never nest deeper, never put a SKILL.md directly under
  a domain folder.
- Skill names are kebab-case, must match their directory name, and must be
  unique across the WHOLE repo (installed links are flattened, dropping the
  domain level). Frontmatter contract: `skills.schema.json`.
- Retired skills move to `deprecated/` at the repo root — never leave them
  under `skills/`, because everything under `skills/` gets installed (and
  would ship in a future Codex plugin, which discovers SKILL.md recursively).
- A skill for one harness only gets an empty marker file in its directory:
  `.claude-only` or `.codex-only`.

## When adding or editing a skill

1. Copy `templates/skill-template/SKILL.md` into the right domain folder.
2. `description` starts with "Use when...", describes ONLY triggering
   conditions (symptoms, keywords, error messages — Vietnamese triggers
   welcome), and NEVER summarizes the skill's workflow.
3. Run `scripts/validate.sh` — it must pass before committing.
4. Update the skill index in `README.md`.
5. No install step is needed after edits: links are symlinks. Run
   `scripts/install.sh` only when a skill is added, renamed, or removed.

## Useful commands

- `scripts/validate.sh` — frontmatter + naming + uniqueness checks
- `scripts/install.sh [--dry-run] [--force]` — (re)link skills into both harnesses
- `scripts/list.sh` — list skills by domain with descriptions
