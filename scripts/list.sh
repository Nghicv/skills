#!/usr/bin/env bash
set -euo pipefail

# Lists every skill grouped by domain, with its description.

REPO="$(cd "$(dirname "$0")/.." && pwd)"

current_domain=""
while IFS= read -r -d '' skill_md; do
  dir="$(dirname "$skill_md")"
  domain="$(basename "$(dirname "$dir")")"
  name="$(basename "$dir")"
  description="$(awk '
    NR == 1 && $0 == "---" { in_fm = 1; next }
    in_fm && $0 == "---" { exit }
    in_fm && collecting {
      if ($0 ~ /^[[:space:]]+[^[:space:]]/) {
        sub(/^[[:space:]]+/, "")
        val = val (val == "" ? "" : " ") $0
        next
      }
      exit
    }
    in_fm && /^description:/ {
      sub(/^description:[[:space:]]*/, "")
      gsub(/^["'\'']|["'\'']$/, "")
      if ($0 != "") { print; exit }
      collecting = 1
      next
    }
    END { if (collecting) print val }
  ' "$skill_md")"

  if [ "$domain" != "$current_domain" ]; then
    printf '\n%s/\n' "$domain"
    current_domain="$domain"
  fi
  printf '  %-40s %s\n' "$name" "$description"
done < <(find "$REPO/skills" -mindepth 3 -maxdepth 3 -name SKILL.md -print0 | sort -z)
