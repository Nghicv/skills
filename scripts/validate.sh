#!/usr/bin/env bash
set -euo pipefail

# Validates every skill in skills/<domain>/<skill-name>/ against the repo rules
# (see skills.schema.json for the canonical frontmatter contract):
#   1. Each skill directory contains a SKILL.md with YAML frontmatter.
#   2. Frontmatter has non-empty `name` and `description`.
#   3. `name` is kebab-case and matches the directory name.
#   4. `description` is at most 1024 characters.
#   5. Skill names are unique across the whole repo (links are flattened).
#
# Exits non-zero if any check fails. Run before committing a new skill.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
errors=0
fail() { echo "FAIL: $1" >&2; errors=$((errors + 1)); }

# frontmatter <file> <key> — print the value of a top-level frontmatter key.
frontmatter() {
  awk -v key="$2" '
    NR == 1 && $0 == "---" { in_fm = 1; next }
    in_fm && $0 == "---" { exit }
    in_fm && $0 ~ "^" key ":" {
      sub("^" key ":[[:space:]]*", "")
      gsub(/^["'\'']|["'\'']$/, "")
      print
      exit
    }
  ' "$1"
}

declare -a seen_names seen_paths

# Skill directories missing SKILL.md entirely.
while IFS= read -r -d '' dir; do
  [ -f "$dir/SKILL.md" ] || fail "$dir has no SKILL.md"
done < <(find "$REPO/skills" -mindepth 2 -maxdepth 2 -type d -print0 | sort -z)

while IFS= read -r -d '' skill_md; do
  dir="$(dirname "$skill_md")"
  rel="${skill_md#"$REPO"/}"
  dirname_="$(basename "$dir")"

  head -n1 "$skill_md" | grep -qx -- '---' || { fail "$rel: missing YAML frontmatter"; continue; }

  name="$(frontmatter "$skill_md" name)"
  description="$(frontmatter "$skill_md" description)"

  [ -n "$name" ] || fail "$rel: frontmatter missing 'name'"
  [ -n "$description" ] || fail "$rel: frontmatter missing 'description'"

  if [ -n "$name" ]; then
    echo "$name" | grep -Eqx '[a-z0-9]+(-[a-z0-9]+)*' \
      || fail "$rel: name '$name' is not kebab-case"
    [ "$name" = "$dirname_" ] \
      || fail "$rel: name '$name' does not match directory name '$dirname_'"

    for i in "${!seen_names[@]}"; do
      if [ "${seen_names[$i]}" = "$name" ]; then
        fail "$rel: duplicate skill name '$name' (also in ${seen_paths[$i]}) — links are flattened, names must be unique repo-wide"
      fi
    done
    seen_names+=("$name")
    seen_paths+=("$rel")
  fi

  if [ -n "$description" ] && [ "${#description}" -gt 1024 ]; then
    fail "$rel: description is ${#description} chars (max 1024)"
  fi
done < <(find "$REPO/skills" -mindepth 3 -maxdepth 3 -name SKILL.md -print0 | sort -z)

if [ "$errors" -gt 0 ]; then
  echo "$errors problem(s) found." >&2
  exit 1
fi
echo "OK: all skills valid."
