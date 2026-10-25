#!/usr/bin/env python3
"""Ad-hoc App Store Connect API call, for what the Releasefile lanes do not cover.

  asc.py --env APP_ASC GET '/v1/apps?filter[bundleId]=com.example.app'
  asc.py --env APP_ASC --write PATCH /v1/reviewSubmissions/<id> '{"data": {...}}'

Reads <PREFIX>_KEY_ID / _ISSUER_ID / _KEY_PATH from the environment or ./fastlane/.env.
Anything but GET needs --write, so a write is always a deliberate second step.
Needs: pip install pyjwt cryptography requests
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import jwt
import requests


def load_env(prefix):
    env_file = Path("fastlane/.env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"'))
    names = [f"{prefix}_{part}" for part in ("KEY_ID", "ISSUER_ID", "KEY_PATH")]
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        sys.exit(f"Missing {', '.join(missing)}")
    return [os.environ[name] for name in names]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", required=True, help="env prefix of the API key, e.g. APP_ASC")
    parser.add_argument("--write", action="store_true", help="allow POST/PATCH/DELETE")
    parser.add_argument("method", choices=["GET", "POST", "PATCH", "DELETE"])
    parser.add_argument("path")
    parser.add_argument("body", nargs="?")
    args = parser.parse_args()
    if args.method != "GET" and not args.write:
        sys.exit(f"{args.method} writes to App Store Connect: get approval, then re-run with --write")

    key_id, issuer, key_path = load_env(args.env)
    now = int(time.time())
    token = jwt.encode({"iss": issuer, "iat": now, "exp": now + 1100, "aud": "appstoreconnect-v1"},
                       Path(os.path.expanduser(key_path)).read_text(), algorithm="ES256", headers={"kid": key_id})
    url = args.path if args.path.startswith("http") else "https://api.appstoreconnect.apple.com" + args.path
    response = requests.request(args.method, url, json=json.loads(args.body) if args.body else None,
                                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    print(json.dumps(response.json(), indent=1) if response.text else response.status_code)
    if response.status_code >= 400:
        sys.exit(1)


if __name__ == "__main__":
    main()
