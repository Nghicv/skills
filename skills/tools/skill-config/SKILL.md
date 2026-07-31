---
name: skill-config
description: Use when the user wants to list, enable, or disable Claude Code skills — turning off a single skill inside a plugin, bulk-toggling a group (e.g. all claude-seo skills), choosing global vs project scope for an override, or checking which skills are currently off/blocked.
---

# skill-config

Extends the built-in `/skills` menu. ALL reads and writes go through the bundled script — NEVER edit settings JSON by hand and NEVER guess mechanisms from memory.

## Current skill states (auto-captured at invocation)

```!
python3 "$HOME/.claude/skills/skill-config/scripts/skill_config.py" list --compact
```

**Act on the listing above immediately:** render it as compact markdown tables (one section per group, keep index numbers and states, surface any `ERROR:` lines), then list the commands: "tắt 3 5" (by number), "bật seo-audit" (by name), "tắt hết claude-seo" (whole group), "tắt X ở project" (scoped), `check`. Do NOT re-run `list` first — the injected output is fresh. Do NOT open any window.

If the user has used the standalone `skillcfg` menu (separate terminal) and comes back: read `~/.claude/skills/skill-config/.last-tui.json` if present, confirm its `changes` per **step 5**, then delete the file.

## Critical facts (verified against official docs)

| Skill kind | Off mechanism (script picks automatically) | Takes effect |
|---|---|---|
| personal / project skill | `skillOverrides: {"<name>": "off"}` | next session (removed from context + `/` menu) |
| plugin skill | `permissions.deny: ["Skill(<plugin>:<name>)"]` | immediately (invocation blocked; name still costs a few context tokens — only `/plugin disable` removes it fully) |

- `skillOverrides` does **NOT** work for plugin skills. Writing `"plugin:name": "off"` there silently does nothing.
- Deny-wins: a skill turned off at global scope **cannot** be re-enabled by a project file. To re-enable for one project: turn on globally, then off in the other projects.

## Text flow

1. **List** (also for the `check` command):
   ```bash
   python3 {skill_dir}/scripts/skill_config.py list
   ```
   (`{skill_dir}` = this skill's base directory. Script auto-detects `$HOME` and uses cwd as project; pass `--project <dir>` if cwd is not the project root.)
2. **Render a table** from the JSON: one section per `group` (personal / project / each plugin), showing `index`, short name, `state` (`on`, `off`, `blocked`, `name-only`, ...), and where any override lives (`state_source.file`). Report any `errors`.
3. **Interpret the user's command** in their language:
   - numbers → map to `name` via `index` from the list you JUST printed (re-run `list` if stale)
   - `tắt hết <plugin>` / `<plugin>:*` → pass the plugin name; `personal` / `project` → group tokens
   - "ở project" / "chỉ project này" → `--scope project`; "global" / "mọi project" → `--scope global`; otherwise omit (auto = where the skill is defined)
4. **Apply**:
   ```bash
   python3 {skill_dir}/scripts/skill_config.py off <full-names...> [--scope ...]
   python3 {skill_dir}/scripts/skill_config.py on  <full-names...>
   ```
5. **Confirm from script output only** — for each change report: skill, file written, mechanism, `effect` (immediate vs next session), and the `.skill-config.bak` backup path. If the script returned `errors` or you cannot verify a change in its output, say so plainly — do not claim success.

## Common mistakes

| Mistake | Reality |
|---|---|
| Putting a plugin skill in `skillOverrides` | Silently ignored. Plugin skills need the deny rule — the script handles this. |
| "Project settings can re-enable a global off" | False. Deny/off wins across scopes. |
| Hand-editing settings.json | Risk of corrupting user config. Script parses, modifies only `skillOverrides` + `Skill(...)` deny rules, backs up first. |
| Reporting success without reading script output | Only the `changes` array proves what was written. |
