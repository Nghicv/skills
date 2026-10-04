#!/usr/bin/env python3
"""Đo rank keyword, ghi measure/<date>.json và append rank-history.csv.

    python3 measure_keywords.py <repo>/aso [--date YYYY-MM-DD] [--force]
"""
import argparse, csv, datetime, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import load, search

HEADER = ["date", "platform", "country", "keyword", "rank", "result_count",
          "metadata_version", "core"]


def current_version(aso_dir):
    """Version metadata mới nhất đã có live_from — dùng để gắn nhãn phép đo."""
    import yaml
    mdir = os.path.join(aso_dir, "metadata")
    best = (None, None)
    for fn in sorted(os.listdir(mdir)) if os.path.isdir(mdir) else []:
        if not fn.endswith((".yml", ".yaml")):
            continue
        with open(os.path.join(mdir, fn), encoding="utf-8") as f:
            m = yaml.safe_load(f) or {}
        lf = m.get("live_from")
        if lf and (best[0] is None or str(lf) > str(best[0])):
            best = (str(lf), m.get("version") or fn.rsplit(".", 1)[0])
    return best[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("aso_dir")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--force", action="store_true", help="ghi đè phép đo cùng ngày")
    ap.add_argument("--delay", type=float, default=1.2, help="giãn cách giữa các query")
    a = ap.parse_args()

    cfg, kws, aso_dir = load(a.aso_dir)
    if not kws:
        sys.exit("keywords.yml rỗng — chưa có gì để đo.")
    adam = str(cfg["app"]["adam_id"])
    mv = current_version(aso_dir)

    out_path = os.path.join(aso_dir, "measure", f"{a.date}.json")
    if os.path.exists(out_path) and not a.force:
        sys.exit(f"Đã có {out_path}. Dùng --force để đo lại.")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    rows, failed = [], 0
    for i, k in enumerate(kws, 1):
        if k.get("status") == "retired":
            continue
        if k.get("platform", "both") not in ("both", "ios"):
            continue
        c, kw = k["c"], k["kw"]
        ids, n = search(kw, c)
        if ids is None:
            failed += 1
            rank, n = None, None
            mark = "LỖI"
        else:
            rank = ids.index(adam) + 1 if adam in ids else None
            mark = f"#{rank}" if rank else "—"
        rows.append({"date": a.date, "platform": "ios", "country": c,
                     "keyword": kw, "rank": rank,
                     "result_count": n, "metadata_version": mv,
                     "core": bool(k.get("core"))})
        print(f"[{i:>3}/{len(kws)}] {c:<3} {kw[:34]:<34} {mark:>5}  "
              f"({n if n is not None else '?'} kết quả)")
        time.sleep(a.delay)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"date": a.date, "method": "itunes-search-api", "limit": 200,
                   "metadata_version": mv, "adam_id": adam,
                   "failed_queries": failed, "ranks": rows},
                  f, ensure_ascii=False, indent=2)

    csv_path = os.path.join(aso_dir, "rank-history.csv")
    existing = []
    if os.path.exists(csv_path):
        with open(csv_path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                r.setdefault("platform", "ios")
                if not (r["date"] == a.date and r.get("platform") == "ios"):
                    existing.append(r)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        for r in existing + rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in HEADER})

    ranked = sum(1 for r in rows if r["rank"])
    print(f"\n{ranked}/{len(rows)} keyword có mặt trong top 200"
          + (f" — {failed} query lỗi" if failed else ""))
    print(f"→ {out_path}\n→ {csv_path}")
    print("\nChạy compare_measures.py để xem thay đổi.")


if __name__ == "__main__":
    main()
