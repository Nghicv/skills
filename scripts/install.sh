#!/usr/bin/env bash
set -euo pipefail

# Links every skill in this repo into the local skill directories used by
# each agent harness:
#   - ~/.claude/skills  — Claude Code
#   - ~/.agents/skills  — Codex, Copilot CLI, Gemini CLI (Agent Skills standard)
#
# Skills live at skills/<domain>/<skill-name>/SKILL.md; links are flattened
# (the <domain> level is dropped) because both harnesses use a flat namespace.
# Each entry is a symlink into this repo, so editing a skill here updates it
# everywhere immediately, and `git pull` is all that's needed to stay current.
#
# Per-tool exclusion markers (place an empty file inside the skill dir):
#   .claude-only  — link only into ~/.claude/skills
#   .codex-only   — link only into ~/.agents/skills
#
# Existing entries that are NOT symlinks into this repo are skipped with a
# warning so unmigrated skills are never clobbered. Use --force to replace.
#
# Usage: scripts/install.sh [--force] [--dry-run]

REPO="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_DEST="$HOME/.claude/skills"
AGENTS_DEST="$HOME/.agents/skills"

FORCE=0
DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    --dry-run) DRY_RUN=1 ;;
    *) echo "usage: $0 [--force] [--dry-run]" >&2; exit 2 ;;
  esac
done

# Refuse to run if a destination is itself a symlink into this repo — we would
# end up writing per-skill links back into our own skills/ tree.
for DEST in "$CLAUDE_DEST" "$AGENTS_DEST"; do
  if [ -L "$DEST" ]; then
    resolved="$(readlink -f "$DEST")"
    case "$resolved" in
      "$REPO"|"$REPO"/*)
        echo "error: $DEST is a symlink into this repo ($resolved)." >&2
        echo "Remove it (rm \"$DEST\") and re-run; it will be recreated as a real directory." >&2
        exit 1
        ;;
    esac
  fi
done

link_skill() {
  local src="$1" dest_dir="$2"
  local name target
  name="$(basename "$src")"
  target="$dest_dir/$name"

  if [ -e "$target" ] || [ -L "$target" ]; then
    if [ -L "$target" ] && [[ "$(readlink -f "$target" || true)" == "$REPO"/* ]]; then
      : # already a link into this repo — refresh it below
    elif [ "$FORCE" -eq 1 ]; then
      echo "replacing $target (--force)"
      [ "$DRY_RUN" -eq 1 ] || rm -rf "$target"
    else
      echo "skip: $target exists and is not managed by this repo (use --force to replace)" >&2
      return 0
    fi
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    echo "would link $name -> $src ($dest_dir)"
  else
    mkdir -p "$dest_dir"
    ln -sfn "$src" "$target"
    echo "linked $name -> $src ($dest_dir)"
  fi
}

count=0
while IFS= read -r -d '' skill_md; do
  src="$(dirname "$skill_md")"
  count=$((count + 1))
  if [ -e "$src/.claude-only" ]; then
    link_skill "$src" "$CLAUDE_DEST"
  elif [ -e "$src/.codex-only" ]; then
    link_skill "$src" "$AGENTS_DEST"
  else
    link_skill "$src" "$CLAUDE_DEST"
    link_skill "$src" "$AGENTS_DEST"
  fi
done < <(find "$REPO/skills" -mindepth 3 -maxdepth 3 -name SKILL.md -print0 | sort -z)

echo "done: $count skill(s) processed."
