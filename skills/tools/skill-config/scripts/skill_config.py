#!/usr/bin/env python3
"""Helper for the /skill-config skill.

Enumerates Claude Code skills (personal, project, plugin) and toggles them:
  - personal/project skills -> settings "skillOverrides": {"<name>": "off"}
  - plugin skills           -> settings "permissions.deny": ["Skill(<plugin>:<name>)"]
    (skillOverrides does not apply to plugin skills per official docs)

Only ever touches those two keys. Backs up each settings file before writing.
Prints JSON to stdout. Python 3 stdlib only.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

OFF_STATES = {"off"}
SKILL_DENY_RE_PREFIX = "Skill("


def load_json(path: Path):
    if not path.is_file():
        return {}, None
    try:
        return json.loads(path.read_text()), None
    except (json.JSONDecodeError, OSError) as e:
        return {}, f"{path}: {e}"


def settings_files(home: Path, project: Path):
    """Settings files in precedence order (low -> high)."""
    return {
        "global": home / ".claude" / "settings.json",
        "project": project / ".claude" / "settings.json",
        "local": project / ".claude" / "settings.local.json",
    }


def skill_deny_rules(settings: dict):
    deny = settings.get("permissions", {}).get("deny", [])
    out = set()
    for rule in deny:
        if isinstance(rule, str) and rule.startswith(SKILL_DENY_RE_PREFIX) and rule.endswith(")"):
            out.add(rule[len(SKILL_DENY_RE_PREFIX):-1].strip())
    return out


def discover(home: Path, project: Path):
    """Return (skills, errors). Each skill: dict with name, group, kind, dir, scope_default."""
    skills, errors = [], []

    def scan_dir(base: Path, kind: str, group: str, scope_default: str, prefix: str = ""):
        if not base.is_dir():
            return
        for d in sorted(base.iterdir()):
            if (d / "SKILL.md").is_file():
                skills.append({
                    "name": prefix + d.name,
                    "short": d.name,
                    "kind": kind,
                    "group": group,
                    "dir": str(d),
                    "scope_default": scope_default,
                })

    scan_dir(home / ".claude" / "skills", "personal", "personal", "global")
    scan_dir(project / ".claude" / "skills", "project", "project", "project")

    # plugins
    installed_path = home / ".claude" / "plugins" / "installed_plugins.json"
    installed, err = load_json(installed_path)
    if err:
        errors.append(err)

    # enabledPlugins merged low->high so higher scope wins
    enabled = {}
    for _, f in settings_files(home, project).items():
        s, err = load_json(f)
        if err:
            errors.append(err)
        enabled.update(s.get("enabledPlugins", {}))

    for plugin_key, entries in installed.get("plugins", {}).items():
        if not enabled.get(plugin_key, False):
            continue
        plugin_name = plugin_key.split("@")[0]
        entry = None
        for e in entries or []:
            if e.get("scope") == "user":
                entry = e
                break
            if e.get("scope") == "project" and Path(e.get("projectPath", "")).resolve() == project.resolve():
                entry = e
        fallback = False
        if entry is None and entries:
            # plugin enabled (e.g. via user-level enabledPlugins) but installed under
            # another project's scope: skills still load, so use the newest install
            entry = max(entries, key=lambda e: e.get("lastUpdated", ""))
            fallback = True
        if entry is None:
            continue
        scope_default = "global" if entry.get("scope") == "user" or fallback else "project"
        scan_dir(Path(entry.get("installPath", "")) / "skills", "plugin",
                 plugin_name, scope_default, prefix=plugin_name + ":")

    return skills, errors


def read_states(home: Path, project: Path):
    """Per settings-scope: (skillOverrides dict, deny-skill set)."""
    states, errors = {}, []
    for scope, f in settings_files(home, project).items():
        s, err = load_json(f)
        if err:
            errors.append(err)
        states[scope] = {
            "file": str(f),
            "overrides": s.get("skillOverrides", {}),
            "deny": skill_deny_rules(s),
        }
    return states, errors


def effective_state(skill, states):
    """Off/blocked wins across scopes; otherwise highest-precedence value."""
    hits = []
    for scope in ("global", "project", "local"):
        st = states[scope]
        if skill["kind"] == "plugin":
            if skill["name"] in st["deny"]:
                hits.append({"scope": scope, "state": "blocked", "mechanism": "deny", "file": st["file"]})
        else:
            ov = st["overrides"].get(skill["short"])
            if ov is not None:
                hits.append({"scope": scope, "state": ov, "mechanism": "skillOverrides", "file": st["file"]})
    for h in hits:  # any off/blocked wins (deny-wins rule)
        if h["state"] in OFF_STATES or h["state"] == "blocked":
            return h["state"], h, hits
    if hits:
        return hits[-1]["state"], hits[-1], hits  # highest precedence non-off
    return "on", None, hits


def cmd_list(home, project, compact=False):
    skills, errors = discover(home, project)
    states, errs2 = read_states(home, project)
    errors += errs2
    out = []
    for i, sk in enumerate(skills, 1):
        state, src, hits = effective_state(sk, states)
        out.append({
            "index": i,
            "name": sk["name"],
            "kind": sk["kind"],
            "group": sk["group"],
            "scope_default": sk["scope_default"],
            "state": state,
            "state_source": src,
            "all_overrides": hits,
        })
    if compact:
        last_group = None
        for s in out:
            if s["group"] != last_group:
                last_group = s["group"]
                print(f"## {s['group']} (scope: {s['scope_default']})")
            src = s["state_source"]
            where = f"  <- {src['file']}" if src else ""
            print(f"{s['index']}. {s['name']} [{s['state']}]{where}")
        for e in errors:
            print(f"ERROR: {e}")
    else:
        print(json.dumps({"skills": out, "errors": errors}, indent=2, ensure_ascii=False))
    return 0


def resolve_names(tokens, skills):
    """Resolve user tokens to skill dicts. Supports full name, bare name, group tokens."""
    resolved, errors = [], []
    by_full = {s["name"]: s for s in skills}
    for tok in tokens:
        tok = tok.strip()
        if tok in by_full:
            resolved.append(by_full[tok])
            continue
        if tok in ("personal", "project"):
            grp = [s for s in skills if s["group"] == tok]
            if not grp:
                errors.append(f"no skills in group '{tok}'")
            resolved += grp
            continue
        if tok.endswith(":*"):
            tok = tok[:-2]
        grp = [s for s in skills if s["kind"] == "plugin" and s["group"] == tok]
        if grp:
            resolved += grp
            continue
        matches = [s for s in skills if s["short"] == tok]
        if len(matches) == 1:
            resolved.append(matches[0])
        elif len(matches) > 1:
            errors.append(f"'{tok}' is ambiguous: " + ", ".join(m["name"] for m in matches))
        else:
            errors.append(f"no skill matches '{tok}'")
    # dedupe preserving order
    seen, unique = set(), []
    for s in resolved:
        if s["name"] not in seen:
            seen.add(s["name"])
            unique.append(s)
    return unique, errors


def write_settings(path: Path, data: dict, backups_done: set):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and str(path) not in backups_done:
        shutil.copy2(path, str(path) + ".skill-config.bak")
        backups_done.add(str(path))
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def target_scope(skill, scope_arg):
    if scope_arg != "auto":
        return scope_arg
    return skill["scope_default"]


def cmd_toggle(home, project, tokens, turn_off, scope_arg, emit=True):
    skills, errors = discover(home, project)
    targets, errs = resolve_names(tokens, skills)
    errors += errs
    files = settings_files(home, project)
    changes = []
    backups_done = set()
    # cache loaded settings per file so multiple edits accumulate
    loaded = {}

    def get(scope):
        if scope not in loaded:
            data, err = load_json(files[scope])
            if err:
                errors.append(err + " (file left untouched)")
                return None
            loaded[scope] = data
        return loaded[scope]

    dirty = set()
    for sk in targets:
        if turn_off:
            scope = target_scope(sk, scope_arg)
            data = get(scope)
            if data is None:
                continue
            if sk["kind"] == "plugin":
                rule = f"Skill({sk['name']})"
                deny = data.setdefault("permissions", {}).setdefault("deny", [])
                if rule not in deny:
                    deny.append(rule)
                    dirty.add(scope)
                changes.append({"skill": sk["name"], "action": "off", "mechanism": "deny",
                                "file": str(files[scope]),
                                "effect": "immediate block; name stays in context until plugin disabled",
                                "already": rule in deny and scope not in dirty})
            else:
                ov = data.setdefault("skillOverrides", {})
                before = ov.get(sk["short"])
                if before != "off":
                    ov[sk["short"]] = "off"
                    dirty.add(scope)
                changes.append({"skill": sk["name"], "action": "off", "mechanism": "skillOverrides",
                                "file": str(files[scope]), "before": before, "after": "off",
                                "effect": "removed from context from next session"})
        else:  # turn on: remove entries. auto -> everywhere found; explicit scope -> only there
            scopes = [scope_arg] if scope_arg != "auto" else ["global", "project", "local"]
            removed_any = False
            for scope in scopes:
                data = get(scope)
                if data is None:
                    continue
                if sk["kind"] == "plugin":
                    rule = f"Skill({sk['name']})"
                    deny = data.get("permissions", {}).get("deny", [])
                    if rule in deny:
                        deny.remove(rule)
                        dirty.add(scope)
                        removed_any = True
                        changes.append({"skill": sk["name"], "action": "on", "mechanism": "deny removed",
                                        "file": str(files[scope]), "effect": "immediate"})
                else:
                    ov = data.get("skillOverrides", {})
                    if sk["short"] in ov:
                        before = ov.pop(sk["short"])
                        dirty.add(scope)
                        removed_any = True
                        changes.append({"skill": sk["name"], "action": "on", "mechanism": "skillOverrides removed",
                                        "file": str(files[scope]), "before": before,
                                        "effect": "back in context from next session"})
            if not removed_any:
                changes.append({"skill": sk["name"], "action": "on", "note": "no off/deny entry found; already on"})

    for scope in dirty:
        write_settings(files[scope], loaded[scope], backups_done)

    result = {"changes": changes, "backups": sorted(backups_done), "errors": errors}
    if emit:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1 if errors else 0
    return result


def cmd_tui(home, project, result_file=None):
    """Interactive curses picker: Space toggles, Enter saves, q cancels.

    Renders on /dev/tty so it works even when stdout is piped (e.g. Claude
    Code's `!` prefix captures stdout); the JSON result still goes to stdout.
    """
    import os
    try:
        tty_fd = os.open("/dev/tty", os.O_RDWR)
    except OSError:
        print(json.dumps({"errors": [
            "no controlling terminal: run this command in a separate terminal window, "
            "then use 'check' here to see the resulting states"]}))
        return 1
    os.environ.setdefault("TERM", "xterm-256color")
    import curses

    skills, errors = discover(home, project)
    states, errs2 = read_states(home, project)
    errors += errs2
    if not skills:
        print(json.dumps({"errors": errors + ["no skills found"]}))
        return 1

    current = {}
    for sk in skills:
        state, _, _ = effective_state(sk, states)
        current[sk["name"]] = state not in ("off", "blocked")
    desired = dict(current)

    rows = []  # ("group", label) | ("skill", skill)
    last_group = None
    for sk in skills:
        if sk["group"] != last_group:
            last_group = sk["group"]
            label = {"personal": "PERSONAL (~/.claude/skills)",
                     "project": "PROJECT (.claude/skills)"}.get(sk["group"], f"PLUGIN: {sk['group']}")
            rows.append(("group", label, sk["group"]))
        rows.append(("skill", sk, sk["group"]))
    skill_rows = [i for i, r in enumerate(rows) if r[0] == "skill"]

    def run(stdscr):
        curses.curs_set(0)
        stdscr.timeout(90000)  # auto-cancel if no keypress for 90s (never hang the session)
        cur = skill_rows[0]
        top = 0
        while True:
            h, w = stdscr.getmaxyx()
            view = h - 2
            if cur < top:
                top = cur
            if cur >= top + view:
                top = cur - view + 1
            stdscr.erase()
            for y, i in enumerate(range(top, min(top + view, len(rows)))):
                kind, data, _ = rows[i]
                if kind == "group":
                    stdscr.addnstr(y, 0, f"── {data} " + "─" * w, w - 1, curses.A_BOLD)
                else:
                    on = desired[data["name"]]
                    changed = "*" if on != current[data["name"]] else " "
                    mark = "[x]" if on else "[ ]"
                    line = f"  {mark}{changed} {data['short']}"
                    attr = curses.A_REVERSE if i == cur else curses.A_NORMAL
                    stdscr.addnstr(y, 0, line.ljust(w - 1), w - 1, attr)
            n_changed = sum(1 for k in desired if desired[k] != current[k])
            help_line = f" Space: toggle · g: cả nhóm · ↑/↓: di chuyển · Enter: lưu ({n_changed} thay đổi) · q: thoát"
            stdscr.addnstr(h - 1, 0, help_line.ljust(w - 1), w - 1, curses.A_REVERSE)
            stdscr.refresh()
            key = stdscr.getch()
            if key in (curses.KEY_DOWN, ord("j")):
                nxt = [i for i in skill_rows if i > cur]
                cur = nxt[0] if nxt else cur
            elif key in (curses.KEY_UP, ord("k")):
                prv = [i for i in skill_rows if i < cur]
                cur = prv[-1] if prv else cur
            elif key == ord(" "):
                name = rows[cur][1]["name"]
                desired[name] = not desired[name]
            elif key == ord("g"):
                grp = rows[cur][2]
                members = [r[1]["name"] for r in rows if r[0] == "skill" and r[2] == grp]
                target = not all(desired[m] for m in members)
                for m in members:
                    desired[m] = target
            elif key in (curses.KEY_ENTER, 10, 13):
                return True
            elif key in (ord("q"), 27) or key == -1:  # -1 = idle timeout
                return False

    saved_in, saved_out = os.dup(0), os.dup(1)
    os.dup2(tty_fd, 0)
    os.dup2(tty_fd, 1)
    try:
        save = curses.wrapper(run)
    finally:
        os.dup2(saved_in, 0)
        os.dup2(saved_out, 1)
        for fd in (saved_in, saved_out, tty_fd):
            os.close(fd)
    if not save:
        result = {"changes": [], "cancelled": True, "errors": errors}
    else:
        to_off = [n for n in desired if current[n] and not desired[n]]
        to_on = [n for n in desired if not current[n] and desired[n]]
        result = {"changes": [], "backups": [], "errors": errors}
        for names, off in ((to_off, True), (to_on, False)):
            if names:
                r = cmd_toggle(home, project, names, off, "auto", emit=False)
                result["changes"] += r["changes"]
                result["backups"] = sorted(set(result["backups"]) | set(r["backups"]))
                result["errors"] += r["errors"]
    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if result_file:
        Path(result_file).write_text(payload + "\n")
    print(payload)
    if result.get("changes"):
        print(f"\nDa luu {len(result['changes'])} thay doi. "
              "Quay lai Claude Code va go 'check' de xac nhan.", file=sys.stderr)
    elif result.get("cancelled"):
        print("\nDa thoat, khong thay doi gi.", file=sys.stderr)
    return 1 if result["errors"] else 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--home", default=str(Path.home()), help="HOME dir (for testing)")
    p.add_argument("--project", default=".", help="project dir")
    sub = p.add_subparsers(dest="cmd", required=True)
    lp = sub.add_parser("list")
    lp.add_argument("--compact", action="store_true")
    tp = sub.add_parser("tui")
    tp.add_argument("--result-file", default=None)
    for name in ("off", "on"):
        sp = sub.add_parser(name)
        sp.add_argument("names", nargs="+")
        sp.add_argument("--scope", choices=["auto", "global", "project", "local"], default="auto")
    args = p.parse_args()

    home, project = Path(args.home), Path(args.project)
    if args.cmd == "list":
        return cmd_list(home, project, compact=args.compact)
    if args.cmd == "tui":
        return cmd_tui(home, project, result_file=args.result_file)
    return cmd_toggle(home, project, args.names, args.cmd == "off", args.scope)


if __name__ == "__main__":
    sys.exit(main())
