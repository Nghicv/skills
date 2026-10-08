#!/usr/bin/env python3
"""Collect one person's commits from a GitHub org, across ALL branches.

Why git and not the REST API: querying commits per branch costs one request
per branch x author x page and exhausts the 5000/h REST quota on a few busy
repos. Instead this lists repos once (`gh repo list`, GraphQL) and keeps a
bare, treeless (`--filter=tree:0`) mirror per repo in a local cache, so each
run is one `git fetch` per repo and `git log --all` does the filtering.

A commit reachable from several branches is reported once.
Output TSV: repo<TAB>sha<TAB>author_date_iso<TAB>author_email<TAB>subject
"""
import argparse, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def list_repos(org, since):
    out = run(["gh", "repo", "list", org, "--limit", "1000", "--no-archived",
               "--json", "name,pushedAt,sshUrl,url"])
    if out.returncode != 0:
        sys.exit(f"gh repo list failed: {out.stderr.strip()}")
    return [r for r in json.loads(out.stdout) if (r["pushedAt"] or "") >= since]

def sync(repo, cache, use_ssh):
    path = os.path.join(cache, repo["name"] + ".git")
    url = repo["sshUrl"] if use_ssh else repo["url"] + ".git"
    if not os.path.isdir(path):
        r = run(["git", "clone", "--bare", "--filter=tree:0", "--quiet", url, path])
    else:
        r = run(["git", "-C", path, "fetch", "--quiet", "--prune", "--filter=tree:0",
                 "origin", "+refs/heads/*:refs/heads/*"])
    return repo["name"], path, r.returncode, r.stderr.strip()[:300]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--since", required=True, help="YYYY-MM-DD (inclusive)")
    ap.add_argument("--until", help="YYYY-MM-DD (inclusive, optional)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", default=os.path.expanduser("~/.cache/git-timesheet"))
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    cfg = json.load(open(a.config))["github"]
    org = cfg["org"]
    emails = {e.lower() for e in cfg.get("author_emails", [])}
    names = set(cfg.get("author_names", []))
    if not emails and not names:
        sys.exit("config github.author_emails / author_names is empty")
    cache = os.path.join(a.cache, org)
    os.makedirs(cache, exist_ok=True)

    repos = list_repos(org, f"{a.since}T00:00:00Z")
    if cfg.get("repos"):
        repos = [r for r in repos if r["name"] in set(cfg["repos"])]
    print(f"{len(repos)} repos pushed since {a.since}; syncing to {cache}", file=sys.stderr)
    with ThreadPoolExecutor(a.workers) as ex:
        synced = list(ex.map(lambda r: sync(r, cache, cfg.get("ssh", True)), repos))
    failed = [s for s in synced if s[2] != 0]

    seen, rows = set(), []
    fmt = "%H%x1f%aI%x1f%ae%x1f%an%x1f%s"
    for name, path, code, _ in synced:
        if code != 0:
            continue
        cmd = ["git", "-C", path, "log", "--all", f"--since={a.since}T00:00:00", f"--format={fmt}"]
        if a.until:
            cmd.append(f"--until={a.until}T23:59:59")
        out = run(cmd)
        for line in out.stdout.splitlines():
            sha, date, email, author, subject = line.split("\x1f", 4)
            if sha in seen or not (email.lower() in emails or author in names):
                continue
            seen.add(sha)
            rows.append((name, sha, date, email, subject.replace("\t", " ")))

    rows.sort(key=lambda x: x[2])
    with open(a.out, "w") as f:
        for row in rows:
            f.write("\t".join(row) + "\n")
    counts = {}
    for row in rows:
        counts[row[0]] = counts.get(row[0], 0) + 1
    for r, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"{n:6d}  {r}", file=sys.stderr)
    print(f"{len(rows)} unique commits -> {a.out}", file=sys.stderr)
    if failed:
        print(f"ERROR: {len(failed)} repo(s) failed to sync — result is INCOMPLETE:", file=sys.stderr)
        for name, _, _, err in failed:
            print(f"  {name}: {err}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
