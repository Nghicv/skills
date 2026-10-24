"""Mirrors screenshot release folders into the app's Google Drive archive.

    python3 drive_sync.py <aso_dir> <release_dir> [<release_dir> ...] [--dry-run] [--account EMAIL] [--folder ID]

The target folder is `screenshots.drive_folder` in <aso_dir>/config.yml (--folder overrides it).

Each release lands as a folder of the same name under the target folder, with its tree mirrored.
Files already there with the same MD5 are skipped; changed ones are overwritten in place (same
Drive id, so shared links keep working). Nothing on Drive is ever deleted.
Auth: the gcloud account's token, which needs Drive access (gcloud auth login --enable-gdrive-access).
"""
import argparse
import hashlib
import json
import mimetypes
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import load  # noqa: E402

FOLDER_MIME = "application/vnd.google-apps.folder"
API = "https://www.googleapis.com/drive/v3"
UPLOAD = "https://www.googleapis.com/upload/drive/v3"
SKIP = {".DS_Store"}


def token(account):
    env = dict(os.environ)
    env.setdefault("CLOUDSDK_PYTHON", "/opt/homebrew/bin/python3.14")
    cmd = ["gcloud", "auth", "print-access-token"] + ([account] if account else [])
    out = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if out.returncode != 0:
        sys.exit("gcloud has no usable login: run `gcloud auth login --enable-gdrive-access`")
    return out.stdout.strip()


TOKEN = None


def call(url, method="GET", body=None, headers=None):
    hdrs = {"Authorization": f"Bearer {TOKEN}"}
    hdrs.update(headers or {})
    if isinstance(body, dict):
        body = json.dumps(body).encode()
        hdrs["Content-Type"] = "application/json"
    r = urllib.request.Request(url, method=method, data=body, headers=hdrs)
    try:
        with urllib.request.urlopen(r, timeout=300) as resp:
            data = resp.read()
            return json.loads(data) if data else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:800]
        if e.code == 403 and "insufficient" in detail.lower():
            sys.exit("The gcloud token has no Drive scope: run `gcloud auth login --enable-gdrive-access`")
        sys.exit(f"{method} {url} -> {e.code}\n{detail}")


def children(folder_id):
    q = urllib.parse.quote(f"'{folder_id}' in parents and trashed = false")
    items, page = [], ""
    while True:
        res = call(f"{API}/files?q={q}&fields=nextPageToken,files(id,name,mimeType,md5Checksum)"
                   f"&pageSize=1000&supportsAllDrives=true&includeItemsFromAllDrives=true{page}")
        items += res.get("files", [])
        if not res.get("nextPageToken"):
            return {f["name"]: f for f in items}
        page = "&pageToken=" + res["nextPageToken"]


def ensure_folder(parent_id, name, dry):
    existing = children(parent_id).get(name)
    if existing and existing["mimeType"] == FOLDER_MIME:
        return existing["id"]
    if dry:
        return None
    return call(f"{API}/files?supportsAllDrives=true", "POST",
                {"name": name, "mimeType": FOLDER_MIME, "parents": [parent_id]})["id"]


def upload(parent_id, path, existing, dry):
    data = open(path, "rb").read()
    name = os.path.basename(path)
    if existing and existing.get("md5Checksum") == hashlib.md5(data).hexdigest():
        return "same"
    if dry:
        return "update" if existing else "new"
    mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
    if existing:
        call(f"{UPLOAD}/files/{existing['id']}?uploadType=media&supportsAllDrives=true", "PATCH", data,
             {"Content-Type": mime})
        return "update"
    boundary = uuid.uuid4().hex
    meta = json.dumps({"name": name, "parents": [parent_id]}).encode()
    body = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode() + meta +
            f"\r\n--{boundary}\r\nContent-Type: {mime}\r\n\r\n".encode() + data + f"\r\n--{boundary}--".encode())
    call(f"{UPLOAD}/files?uploadType=multipart&supportsAllDrives=true", "POST", body,
         {"Content-Type": f"multipart/related; boundary={boundary}"})
    return "new"


def mirror(local_dir, parent_id, dry, counts, prefix=""):
    remote = children(parent_id) if parent_id else {}
    for name in sorted(os.listdir(local_dir)):
        if name in SKIP or name.startswith("."):
            continue
        path = os.path.join(local_dir, name)
        if os.path.isdir(path):
            sub = ensure_folder(parent_id, name, dry) if parent_id else None
            mirror(path, sub, dry, counts, f"{prefix}{name}/")
        else:
            result = upload(parent_id, path, remote.get(name), dry)
            counts[result] = counts.get(result, 0) + 1
            if result != "same":
                print(f"{result:6} {prefix}{name}", flush=True)


def main():
    global TOKEN
    ap = argparse.ArgumentParser()
    ap.add_argument("aso_dir")
    ap.add_argument("releases", nargs="+")
    ap.add_argument("--folder", help="Drive folder id (default: screenshots.drive_folder in config.yml)")
    ap.add_argument("--dry-run", action="store_true")
    # A Drive-only login can sit beside the account gcloud uses for Firebase and GA4.
    ap.add_argument("--account", help="gcloud account to use (default: the active one)")
    args = ap.parse_args()
    cfg, _, _ = load(args.aso_dir)
    args.folder = args.folder or (cfg.get("screenshots") or {}).get("drive_folder")
    if not args.folder:
        sys.exit("No Drive folder: set screenshots.drive_folder in config.yml or pass --folder")
    TOKEN = token(args.account)
    for rel in args.releases:
        rel = os.path.abspath(rel)
        if not os.path.isdir(rel):
            sys.exit(f"not a folder: {rel}")
        counts = {}
        top = ensure_folder(args.folder, os.path.basename(rel), args.dry_run)
        mirror(rel, top, args.dry_run, counts)
        print(f"{os.path.basename(rel)}: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))
              + (" (dry run)" if args.dry_run else ""))
    print(f"https://drive.google.com/drive/folders/{args.folder}")


if __name__ == "__main__":
    main()
