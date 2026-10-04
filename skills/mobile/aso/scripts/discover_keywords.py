#!/usr/bin/env python3
"""Phase 0: đào keyword ứng viên từ autocomplete + chấm độ khó.

    python3 discover_keywords.py <repo>/aso --country us --seed "expense tracker" --seed "ocr"

Ghi research/candidates.csv. Không tự chấm popularity — lấy tay từ Apple Ads
Keyword Planner (5-100), xem references/research.md.
"""
import argparse, csv, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import load, search, hints, sf_header

HEADER = ["country", "keyword", "popularity", "result_count", "top1_app",
          "top1_exact_match", "our_rank", "intent_fit", "verdict"]


def difficulty_note(n):
    if n is None:
        return "?"
    if n <= 50:
        return "dễ"
    if n <= 150:
        return "vừa"
    return "khó"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("aso_dir")
    ap.add_argument("--country", required=True)
    ap.add_argument("--seed", action="append", required=True)
    ap.add_argument("--depth", type=int, default=1, help="số vòng mở rộng autocomplete")
    ap.add_argument("--delay", type=float, default=1.2)
    a = ap.parse_args()

    cfg, _, aso_dir = load(a.aso_dir)
    adam = str(cfg["app"]["adam_id"])
    sf = sf_header(cfg, a.country)

    terms, frontier = set(), list(a.seed)
    for _ in range(max(1, a.depth)):
        nxt = []
        for t in frontier:
            if t in terms:
                continue
            terms.add(t)
            for h in hints(t, sf):
                if h not in terms:
                    nxt.append(h)
            time.sleep(a.delay)
        frontier = nxt
    terms |= set(frontier)
    print(f"{len(terms)} ứng viên sau khi mở rộng autocomplete\n")

    rows = []
    for i, kw in enumerate(sorted(terms), 1):
        ids, n = search(kw, a.country)
        top1, exact, our = "", "", ""
        if ids:
            our = ids.index(adam) + 1 if adam in ids else ""
            try:
                import json, urllib.parse, urllib.request
                from _common import get
                d = get("https://itunes.apple.com/search?" + urllib.parse.urlencode(
                    {"term": kw, "country": a.country, "entity": "software", "limit": 1}))
                r = (d.get("results") or [{}])[0]
                top1 = r.get("trackName", "")
                exact = str(kw.strip().lower() in top1.lower()).lower()
            except Exception:
                pass
        rows.append({"country": a.country, "keyword": kw, "popularity": "",
                     "result_count": n if n is not None else "", "top1_app": top1,
                     "top1_exact_match": exact, "our_rank": our,
                     "intent_fit": "", "verdict": ""})
        print(f"[{i:>3}/{len(terms)}] {kw[:36]:<36} {str(n):>4} kết quả "
              f"({difficulty_note(n)})" + (f"  ta: #{our}" if our else ""))
        time.sleep(a.delay)

    rows.sort(key=lambda r: (r["result_count"] if r["result_count"] != "" else 9999))
    out = os.path.join(aso_dir, "research", "candidates.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    write_header = not os.path.exists(out)
    with open(out, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        if write_header:
            w.writeheader()
        w.writerows(rows)

    print(f"\n→ {out} (sắp xếp theo độ khó tăng dần)")
    print("Còn phải điền tay: popularity (Apple Ads), intent_fit, verdict.")
    print("Quy tắc: top1_exact_match = true → SKIP, dù popularity cao mấy.")


if __name__ == "__main__":
    main()
