#!/usr/bin/env python3
"""So sánh rank hai chiều: vs baseline và vs lần đo trước.

    python3 compare_measures.py <repo>/aso [--out reports/<date>-compare.md]
"""
import argparse, csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import load


def read_history(aso_dir):
    p = os.path.join(aso_dir, "rank-history.csv")
    if not os.path.exists(p):
        sys.exit("Chưa có rank-history.csv — chạy measure_keywords.py trước.")
    by_date = {}
    with open(p, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rank = int(r["rank"]) if r["rank"] else None
            plat = r.get("platform") or "ios"
            by_date.setdefault(plat, {}).setdefault(r["date"], {})[(r["country"], r["keyword"])] = {
                "rank": rank,
                "result_count": int(r["result_count"]) if r["result_count"] else None,
                "core": r.get("core", "").lower() == "true",
                "mv": r.get("metadata_version", ""),
            }
    return by_date


def delta_rows(old, new):
    up, down, entered, dropped, same = [], [], [], [], []
    for key, n in new.items():
        o = old.get(key)
        if o is None:
            continue
        a, b = o["rank"], n["rank"]
        if a is None and b is None:
            continue
        if a is None and b is not None:
            entered.append((key, b, n["core"]))
        elif a is not None and b is None:
            dropped.append((key, a, n["core"]))
        elif b < a:
            up.append((key, a, b, a - b, n["core"]))
        elif b > a:
            down.append((key, a, b, b - a, n["core"]))
        else:
            same.append((key, b, n["core"]))
    up.sort(key=lambda x: -x[3])
    down.sort(key=lambda x: -x[3])
    entered.sort(key=lambda x: x[1])
    return up, down, entered, dropped, same


def section(title, up, down, entered, dropped, same):
    L = [f"\n## {title}\n"]
    if up:
        L.append("**Lên hạng**\n")
        L += [f"- {'CORE ' if c else ''}{k[0]}/{k[1]}: {a} → {b} (+{d})"
              for k, a, b, d, c in up]
    if entered:
        L.append("\n**Mới vào top 200**\n")
        L += [f"- {'CORE ' if c else ''}{k[0]}/{k[1]} → #{b}" for k, b, c in entered]
    if down:
        L.append("\n**Tụt hạng**\n")
        L += [f"- {'CORE ' if c else ''}{k[0]}/{k[1]}: {a} → {b} (−{d})"
              for k, a, b, d, c in down]
    if dropped:
        L.append("\n**Rớt khỏi top 200**\n")
        L += [f"- {'CORE ' if c else ''}{k[0]}/{k[1]}: {a} → mất" for k, a, c in dropped]
    L.append(f"\nGiữ nguyên: {len(same)}")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("aso_dir")
    ap.add_argument("--out")
    a = ap.parse_args()

    cfg, _, aso_dir = load(a.aso_dir)
    all_hist = read_history(aso_dir)
    sections, latest_any = [], None
    for plat in sorted(all_hist):
        hist = all_hist[plat]
        dates = sorted(hist)
        if len(dates) < 2:
            sections.append(f"\n# {plat.upper()}\n\nChưa đủ 2 phép đo để so sánh.")
            continue
        sections.append(build(cfg, hist, dates, plat))
        latest_any = latest_any or dates[-1]
    text = "\n".join(sections) + "\n"
    out = a.out or os.path.join(aso_dir, "reports", f"{latest_any}-compare.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    print(f"→ {out}")


def build(cfg, hist, dates, plat):
    a_out = None
    if len(dates) < 2:
        sys.exit("Cần ít nhất 2 phép đo để so sánh.")

    baseline = str(cfg.get("baseline") or dates[0])
    if baseline not in hist:
        print(f"! baseline {baseline} không có trong lịch sử, dùng {dates[0]}")
        baseline = dates[0]
    latest, prev = dates[-1], dates[-2]

    md = [f"\n# {plat.upper()} — đối chiếu rank ({latest})", "",
          f"- Baseline: **{baseline}**",
          f"- Lần đo trước: **{prev}**",
          f"- Metadata version: **{hist[latest][list(hist[latest])[0]]['mv'] or '?'}**"]

    if plat == "android":
        md.append("\n> Độ sâu đo trên Play chỉ ~20-30 kết quả. `mất` ở đây nghĩa là "
                  "**rơi khỏi phần hiển thị**, không phải ngoài top 200.")
    md.append(section(f"So với baseline ({baseline} → {latest})",
                      *delta_rows(hist[baseline], hist[latest])))
    md.append(section(f"Đợt vừa rồi ({prev} → {latest})",
                      *delta_rows(hist[prev], hist[latest])))

    # cảnh báo rollback
    rb = cfg.get("rollback") or {}
    thr = rb.get("threshold_positions")
    breaches = []
    if thr:
        for key, n in hist[latest].items():
            if not n["core"]:
                continue
            b = hist[baseline].get(key)
            if not b or b["rank"] is None:
                continue
            if n["rank"] is None:
                breaches.append(f"{key[0]}/{key[1]}: {b['rank']} → mất hạng")
            elif n["rank"] - b["rank"] > thr:
                breaches.append(f"{key[0]}/{key[1]}: {b['rank']} → {n['rank']}")
    md.append("\n## Ngưỡng rollback\n")
    if breaches:
        md.append(f"**CHẠM NGƯỠNG** (CORE tụt quá {thr} bậc so với baseline):\n")
        md += [f"- {b}" for b in breaches]
        md.append(f"\nCần xác nhận bằng phép đo thứ hai cách nhau "
                  f"{rb.get('sustained_days', 7)} ngày trước khi rollback về "
                  f"{rb.get('to', 'bản trước')}.")
    else:
        md.append("Không có CORE keyword nào chạm ngưỡng.")

    # chan doan index vs rank
    notidx = [f"- {k[0]}/{k[1]}: trả về {n['result_count']} kết quả, app không có trong đó"
              for k, n in hist[latest].items()
              if n["rank"] is None and n["result_count"] and n["result_count"] < 200]
    if notidx:
        md.append("\n## Không được index (không phải hạng thấp)\n")
        md.append("Truy vấn trả về **dưới** 200 kết quả mà app vẫn không có mặt — "
                  "đây là vấn đề relevance/eligibility, không phải popularity.\n")
        md += notidx

    return "\n".join(md)


if __name__ == "__main__":
    main()
