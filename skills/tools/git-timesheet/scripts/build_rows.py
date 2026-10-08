#!/usr/bin/env python3
"""Turn a commit TSV into weekly per-project effort rows (JSON).

Period rules
- Weeks run Monday-Sunday and are cut at month boundaries, so one calendar
  week that spans two months becomes two rows-groups.
- Week hours = hours_per_day x (days with >=1 commit),
  floored at hours_per_day x min(floor_workdays, weekdays in the segment),
  capped at hours_per_day x calendar days in the segment.
- Each commit day is split between projects by that day's commit share, then
  the week total is distributed by the summed shares. Rounding drift goes to
  the largest project so the week sums exactly.
"""
import argparse, collections, datetime as dt, json, re, sys

def month_end(d):
    return (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)

def segments(start, end):
    d = start
    while d <= end:
        e = min(d + dt.timedelta(days=6 - d.weekday()), month_end(d), end)
        yield d, e
        d = e + dt.timedelta(days=1)

def classify(subjects, rules, default):
    votes = collections.Counter()
    for s in subjects:
        s = s.lower().strip()
        if s.startswith("merge"):
            continue
        for kind, prefixes in rules.items():
            if any(re.match(rf"{re.escape(p)}\b", s) for p in prefixes):
                votes[kind] += 1
                break
    return votes.most_common(1)[0][0] if votes else default

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--commits", required=True)
    ap.add_argument("--since", required=True)
    ap.add_argument("--until", required=True)
    ap.add_argument("--today", default=dt.date.today().isoformat())
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    pmap, names = cfg["projects"], cfg.get("project_names", {})
    h = cfg.get("hours", {})
    per_day, floor_wd = h.get("per_day", 8), h.get("floor_workdays", 5)
    wt = cfg.get("work_types", {})
    rules, default_kind = wt.get("rules", {}), wt.get("default", "Feature")
    st = cfg.get("status", {})
    done, doing = st.get("done", "Done"), st.get("in_progress", "Doing")
    tz = dt.timezone(dt.timedelta(hours=cfg.get("timezone_offset_hours", 0)))
    start, end = dt.date.fromisoformat(a.since), dt.date.fromisoformat(a.until)
    today = dt.date.fromisoformat(a.today)

    day = collections.defaultdict(lambda: collections.defaultdict(list))
    unmapped = collections.Counter()
    for line in open(a.commits):
        repo, _sha, date, _email, subject = line.rstrip("\n").split("\t", 4)
        d = dt.datetime.fromisoformat(date.replace("Z", "+00:00")).astimezone(tz).date()
        if not start <= d <= end:
            continue
        if repo not in pmap:
            unmapped[repo] += 1
            continue
        if pmap[repo] is None:  # explicitly excluded repo
            continue
        day[d][pmap[repo]].append((repo, subject))
    if unmapped:
        print("UNMAPPED repos (add to config 'projects', or map to null to exclude):", file=sys.stderr)
        for r, n in unmapped.most_common():
            print(f"  {r}: {n} commits", file=sys.stderr)
        sys.exit(2)

    rows = []
    for s, e in segments(start, end):
        days = [s + dt.timedelta(i) for i in range((e - s).days + 1)]
        active = [x for x in days if x in day]
        if not active:
            continue
        weekdays = sum(x.weekday() < 5 for x in days)
        total = per_day * len(active)
        total = max(total, per_day * min(floor_wd, weekdays))
        total = min(total, per_day * len(days))
        share = collections.Counter()
        info = collections.defaultdict(lambda: {"n": 0, "days": set(), "repos": set(), "subj": []})
        for x in active:
            n = sum(len(v) for v in day[x].values())
            for proj, lst in day[x].items():
                share[proj] += len(lst) / n
                i = info[proj]
                i["n"] += len(lst); i["days"].add(x)
                i["repos"].update(r for r, _ in lst); i["subj"] += [m for _, m in lst]
        tot = sum(share.values())
        projs = sorted(share, key=lambda p: -share[p])
        hrs = {p: round(total * share[p] / tot, 1) for p in projs}
        hrs[projs[0]] = round(hrs[projs[0]] + total - sum(hrs.values()), 1)
        in_progress = s <= today <= e or (e == end and end >= today - dt.timedelta(days=today.weekday()))
        for p in projs:
            i = info[p]
            rows.append({
                "month": s.strftime(cfg.get("month_format", "%m")),
                "start": s.isoformat(), "end": e.isoformat(),
                "project": p, "project_name": names.get(p, p),
                "work_type": classify(i["subj"], rules, default_kind),
                "hours": hrs[p], "percent": round(hrs[p] / total, 2),
                "status": doing if in_progress else done,
                "note": cfg.get("note_format", "{commits} commits / {days} days · {repos}").format(
                    commits=i["n"], days=len(i["days"]),
                    repos=", ".join(sorted(i["repos"], key=str.lower))),
            })
    json.dump(rows, open(a.out, "w"), ensure_ascii=False, indent=1)
    for r in rows:
        print(" | ".join(str(r[k]) for k in
              ("month", "start", "end", "project", "work_type", "hours", "percent", "status", "note")))

if __name__ == "__main__":
    main()
