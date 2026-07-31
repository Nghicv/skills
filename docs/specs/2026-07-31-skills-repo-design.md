# Skills repo design — 2026-07-31

## Goal

One personal repo as the single source of truth for Agent Skills used across
product development (android, ios, mobile, backend, frontend, workflow, tools),
consumable by both Claude Code and Codex without maintaining two formats.

## Decisions

1. **One format, two consumers.** Both Claude Code and Codex (≥0.28) read the
   Agent Skills standard (`SKILL.md` + `name`/`description` frontmatter). Skills
   are written once; only the read location differs (`~/.claude/skills` vs
   `~/.agents/skills`).
2. **Domain-grouped layout:** `skills/<domain>/<skill-name>/SKILL.md`. Chosen
   over a flat prefix layout for browsability. Validated against
   mattpocock/skills (same bucketed layout + link script) and chrisbanes/skills
   (flat layout, chosen there to enable a native Codex plugin).
3. **Distribution: symlink script** (`scripts/install.sh`), flattening the
   domain level into both harness directories. Existing unmanaged entries are
   skipped with a warning (`--force` to replace); refuses to run if a
   destination dir is itself a symlink into the repo.
4. **Uniqueness rule:** flattening requires repo-wide unique skill names;
   `scripts/validate.sh` enforces this plus the frontmatter contract in
   `skills.schema.json` (kebab-case name matching directory, description ≤1024).
5. **Per-tool exclusion** via empty marker files `.claude-only` / `.codex-only`
   inside a skill directory. No marker = installed for both.
6. **`deprecated/` lives OUTSIDE `skills/`** so retired skills are never linked
   and would never ship in a future Codex plugin (Codex discovers SKILL.md
   recursively under a single path and drops symlinks when installing plugins —
   learned from mattpocock's ADR 0002).
7. **Deferred (YAGNI):** `.claude-plugin/` + `.codex-plugin/` manifests, CI
   lint, releases/versioning. Only needed if the set is ever shared for others
   to install as a plugin; current structure keeps that path open.
8. **Migration is selective:** existing skills in `~/.claude/skills` and
   `~/.agents/skills` will be reviewed one by one by the owner and moved into
   the repo; the old locations keep whatever isn't migrated (install.sh's
   skip-unmanaged behavior protects them).

## Conventions

- `description`: third person, starts with "Use when...", triggers only (never
  a workflow summary), Vietnamese trigger keywords welcome.
- Template: `templates/skill-template/SKILL.md`. Agent-facing rules: `AGENTS.md`
  (with `CLAUDE.md` symlinked to it).
