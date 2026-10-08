---
name: git-timesheet
description: Use when the user needs to fill a timesheet, effort-allocation or "% effort per project" spreadsheet from their own git activity — weekly hours per app/project derived from commits in a GitHub org, appended to an .xlsx tracking file (often a Google Sheets export with protected formulas). Triggers on timesheet, effort report, log giờ, chấm công, "điền file theo dõi công việc", "phần trăm effort dự án", "tổng hợp công việc từ commit", "collect dữ liệu của tôi từ org".
---

# git-timesheet

Derive weekly per-project effort from one person's commits and append it to a
spreadsheet — without losing anything else in the workbook.

All person/company specifics (org, author emails, repo → project mapping,
sheet layout) live in a **private config outside this repo**:
`~/.config/git-timesheet/<profile>.json`. Never write them into the skill.
Start from `references/config.example.json`.

## Steps

1. **Pick the profile.** `ls ~/.config/git-timesheet/`. None yet → copy
   `references/config.example.json`, then fill it with the user: org, the
   author **emails** that are really theirs (ask — people often have a second
   identity that must NOT be counted), timezone, target sheet and column
   letters. Inspect the workbook first (header row, hidden columns, any
   "append from row N / do not edit old rows" note) — do not guess the layout.
2. **Find where the log stops** (never re-log existing periods):
   ```bash
   python3 {skill_dir}/scripts/xlsx_append.py last-end --config <cfg>
   ```
   Use the day after as `--since`, unless the user asked for a range that is
   not yet logged.
3. **Collect commits** (all branches, deduped; `gh` must be logged in):
   ```bash
   python3 {skill_dir}/scripts/collect_commits.py --config <cfg> --since <YYYY-MM-DD> --out commits.tsv
   ```
   First run clones bare treeless mirrors into `~/.cache/git-timesheet/` and
   takes a couple of minutes; later runs only fetch. Exit code 1 = some repo
   failed to sync → the data is incomplete, fix it before going on.
4. **Build rows:**
   ```bash
   python3 {skill_dir}/scripts/build_rows.py --config <cfg> --commits commits.tsv \
     --since <start> --until <today> --out rows.json
   ```
   Exit 2 lists repos with no project mapping → ask the user which project
   each belongs to (or `null` to exclude), add to the config, re-run. Show the
   printed table to the user before writing.
5. **Write:** `xlsx_append.py append --config <cfg> --rows rows.json --dry-run`,
   then without `--dry-run`. It appends after the last used row, copies cell
   styles from the person's previous row, and keeps a `.bak`.
6. **Hand-off:** if the user pastes into an online sheet instead,
   `xlsx_append.py tsv --config <cfg> --rows rows.json | pbcopy` (macOS) gives
   tab-separated text in sheet column order, hidden columns included.

## How hours are computed (`build_rows.py`)

| Rule | Value |
|---|---|
| Period | Mon–Sun week, cut at month boundaries |
| Week total | `per_day` × days with ≥1 commit |
| Floor / cap | ≥ `per_day` × min(`floor_workdays`, weekdays in segment); ≤ `per_day` × calendar days |
| Split | each active day split by that day's commit share per project |
| Status | segment containing today (or the open current week) → `in_progress`, else `done` |
| Work type | majority vote of commit-subject prefixes (`work_types.rules`) |

Tell the user the work type is a heuristic and worth a glance.

## Common mistakes

| Mistake | Reality |
|---|---|
| Querying the REST API per branch | Burns the 5000/h quota in minutes and fails silently mid-run → undercount. The script uses git mirrors instead. |
| Matching authors by GitHub login or git name | Names collide across identities. Match on the emails the user confirmed. |
| Re-saving the workbook with openpyxl/pandas | Drops Google-Sheets extensions, validations, array formulas. `xlsx_append.py` edits only the sheet XML. |
| Rewriting already-logged periods | Shared trackers usually forbid editing old rows. Append only; report discrepancies instead of fixing them. |
| Committing the config | It identifies the person, org and projects. It stays in `~/.config/`. |
