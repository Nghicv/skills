#!/usr/bin/env python3
"""Đo rank keyword trên Google Play, append vào rank-history.csv.

    python3 measure_play.py <repo>/aso [--date YYYY-MM-DD] [--force]

GIỚI HẠN QUAN TRỌNG — khác hẳn bản iOS:
  * Trang search Play chỉ render ~20-30 kết quả đầu. Ngoài khoảng đó ghi là None,
    KHÔNG có nghĩa "ngoài top 200" như bên iOS.
  * Không có result_count thật → heuristic độ khó của iOS KHÔNG dùng được ở đây.
  * Scrape HTML nên dễ vỡ khi Google đổi markup. Kiểm depth trước khi tin số liệu.
"""
import argparse, csv, datetime, gzip, json, os, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import load

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")
HEADER = ["date", "platform", "country", "keyword", "rank", "result_count",
          "metadata_version", "core"]


def play_search(term, gl, hl="en", retries=3):
    """Trả về danh sách package theo thứ tự xuất hiện."""
    url = ("https://play.google.com/store/search?"
           + urllib.parse.urlencode({"q": term, "c": "apps", "gl": gl, "hl": hl}))
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA, "Accept-Language": f"{hl}-{gl},{hl};q=0.9",
                "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                html = raw.decode("utf-8", "replace")
            pkgs = []
            for m in re.finditer(r"/store/apps/details\?id=([A-Za-z0-9_.]+)", html):
                p = m.group(1)
                if p not in pkgs:
                    pkgs.append(p)
            return pkgs
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(3 * (attempt + 1))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("aso_dir")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--delay", type=float, default=2.5)
    a = ap.parse_args()

    cfg, kws, aso_dir = load(a.aso_dir)
    pkg = (cfg.get("app") or {}).get("package_name")
    if not pkg:
        sys.exit("config.yml thiếu app.package_name — bắt buộc để đo Play.")
    mv = (cfg.get("android") or {}).get("metadata_version", "")

    out_path = os.path.join(aso_dir, "measure", f"{a.date}-android.json")
    if os.path.exists(out_path) and not a.force:
        sys.exit(f"Đã có {out_path}. Dùng --force để đo lại.")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    target = [k for k in kws
              if k.get("platform", "both") in ("both", "android")
              and k.get("status") != "retired"]
    if not target:
        sys.exit("Không có keyword nào gắn platform android/both trong keywords.yml")

    rows, depths, failed = [], [], 0
    for i, k in enumerate(target, 1):
        c, kw = k["c"], k["kw"]
        pkgs = play_search(kw, c.upper())
        if pkgs is None:
            failed += 1
            rank, depth, mark = None, None, "LỖI"
        else:
            depth = len(pkgs)
            depths.append(depth)
            rank = pkgs.index(pkg) + 1 if pkg in pkgs else None
            mark = f"#{rank}" if rank else "—"
        rows.append({"date": a.date, "platform": "android", "country": c, "keyword": kw,
                     "rank": rank, "result_count": depth, "metadata_version": mv,
                     "core": bool(k.get("core"))})
        print(f"[{i:>3}/{len(target)}] {c:<3} {kw[:34]:<34} {mark:>5}  "
              f"(thấy {depth if depth is not None else '?'} app)")
        time.sleep(a.delay)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"date": a.date, "platform": "android",
                   "method": "play-web-search-scrape", "package_name": pkg,
                   "metadata_version": mv, "failed_queries": failed,
                   "caveat": "chỉ thấy ~20-30 kết quả đầu; rank=null KHÔNG phải "
                             "'ngoài top 200'. result_count là độ sâu render, "
                             "không phải tổng số kết quả.",
                   "ranks": rows}, f, ensure_ascii=False, indent=2)

    csv_path = os.path.join(aso_dir, "rank-history.csv")
    existing = []
    if os.path.exists(csv_path):
        with open(csv_path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                r.setdefault("platform", "ios")
                if not (r["date"] == a.date and r.get("platform") == "android"):
                    existing.append(r)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        for r in existing + rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in HEADER})

    ranked = sum(1 for r in rows if r["rank"])
    avg = sum(depths) / len(depths) if depths else 0
    print(f"\n{ranked}/{len(rows)} keyword lọt vào phần hiển thị"
          + (f" — {failed} query lỗi" if failed else ""))
    print(f"Độ sâu trung bình: {avg:.0f} app. Ngoài khoảng này là mù, không phải mất hạng.")
    print(f"→ {out_path}\n→ {csv_path}")


if __name__ == "__main__":
    main()
