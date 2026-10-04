#!/usr/bin/env python3
"""Kiểm metadata trước khi submit. Luật khác nhau theo nền tảng.

    python3 validate_metadata.py <repo>/aso/metadata/v2.0.yml [--aso-dir <repo>/aso]

iOS     : title 30 / subtitle 30 / keywords 100 + cảnh báo LẶP TỪ (lặp là phí)
Android : title 30 / short_description 80 / full_description 4000
          + kiểm MẬT ĐỘ (Play cần lặp có chừng mực — ngược iOS)

Exit code != 0 nếu có lỗi chặn.
"""
import argparse, csv, os, re, sys
import yaml

LIMITS = {
    "ios":     {"title": 30, "subtitle": 30, "keywords": 100},
    "android": {"title": 30, "short_description": 80, "full_description": 4000},
}
STOP = {"app", "the", "a", "for", "and", "of", "with", "to", "in"}
DENSITY_TARGET = 250  # ~1 lần khớp chính xác mỗi 250 ký tự description


CJK = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")


def words(s):
    return {w for w in re.split(r"[\s,]+", (s or "").lower()) if w and w not in STOP}


def dup_tokens(title, subtitle, keywords):
    """Từ trong keywords đã có ở title/subtitle.

    Ngôn ngữ CJK không có khoảng trắng nên tách token là vô nghĩa — phải so chuỗi con.
    """
    haystack = f"{title} {subtitle}".lower()
    out = set()
    for kw in re.split(r"[,]+", (keywords or "")):
        kw = kw.strip().lower()
        if not kw:
            continue
        if CJK.search(kw):
            if kw in haystack:
                out.add(kw)
        else:
            for w in words(kw):
                if w in (words(title) | words(subtitle)):
                    out.add(w)
    return out


def check_ios(loc, d, errors, warns):
    t, s, k = d.get("title", ""), d.get("subtitle", ""), d.get("keywords", "")
    for field, val in (("title", t), ("subtitle", s), ("keywords", k)):
        n, lim = len(val), LIMITS["ios"][field]
        print(f"   {field+':':<19} {n:>4}/{lim}{'  LỖI' if n > lim else ''}")
        if n > lim:
            errors.append(f"{loc}.{field}: {n}/{lim} ký tự — vượt giới hạn")
    dup = dup_tokens(t, s, k)
    if dup:
        wasted = sum(len(w) + 1 for w in dup)
        warns.append(f"{loc}: keywords lặp từ đã có ở title/subtitle {sorted(dup)} "
                     f"(~{wasted} ký tự lãng phí)")
        print(f"   {'lặp:':<19} {sorted(dup)}  ~{wasted} ký tự")
    if ", " in k or " ," in k:
        warns.append(f"{loc}.keywords: có khoảng trắng quanh dấu phẩy — phí ký tự")
    free = LIMITS["ios"]["keywords"] - len(k)
    if free >= 25:
        warns.append(f"{loc}.keywords: bỏ trống {free}/100 ký tự")


def check_android(loc, d, errors, warns, focus):
    t = d.get("title", "")
    sd = d.get("short_description", "")
    fd = d.get("full_description", "")
    for field, val in (("title", t), ("short_description", sd), ("full_description", fd)):
        n, lim = len(val), LIMITS["android"][field]
        print(f"   {field+':':<19} {n:>4}/{lim}{'  LỖI' if n > lim else ''}")
        if n > lim:
            errors.append(f"{loc}.{field}: {n}/{lim} ký tự — vượt giới hạn")
    if not sd:
        errors.append(f"{loc}: thiếu short_description — trường trọng số cao nhất sau title")
    for kw in focus:
        kwl = kw.lower()
        n_fd = fd.lower().count(kwl)
        ideal = max(1, len(fd) // DENSITY_TARGET)
        where = []
        if kwl in t.lower():
            where.append("title")
        if kwl in sd.lower():
            where.append("short")
        print(f"   ~ \"{kw}\": {n_fd}x trong full (gợi ý ~{ideal}x)"
              f"{'  ở ' + '+'.join(where) if where else '  KHÔNG ở title/short'}")
        if not where:
            warns.append(f"{loc}: từ khoá chính \"{kw}\" không có trong title lẫn "
                         f"short_description")
        if n_fd > ideal * 2.5 and n_fd > 4:
            warns.append(f"{loc}: \"{kw}\" xuất hiện {n_fd}x trong full_description "
                         f"(gợi ý ~{ideal}x) — nguy cơ bị coi là nhồi từ khoá")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metadata_file")
    ap.add_argument("--aso-dir")
    ap.add_argument("--focus", action="append", default=[],
                    help="từ khoá chính cần kiểm mật độ (Android); lặp lại được")
    a = ap.parse_args()

    aso_dir = a.aso_dir or os.path.dirname(os.path.dirname(os.path.abspath(a.metadata_file)))
    with open(a.metadata_file, encoding="utf-8") as f:
        m = yaml.safe_load(f)
    plat = (m.get("platform") or "ios").lower()
    if plat not in LIMITS:
        sys.exit(f"platform '{plat}' không hợp lệ — dùng ios hoặc android")

    errors, warns = [], []
    print(f"# {m.get('version','?')}  [{plat}]  (ship trong {m.get('shipped_in','?')})\n")

    focus = a.focus
    if plat == "android" and not focus:
        kwp = os.path.join(aso_dir, "keywords.yml")
        if os.path.exists(kwp):
            with open(kwp, encoding="utf-8") as f:
                focus = [k["kw"] for k in (yaml.safe_load(f) or []) if k.get("core")][:3]

    for loc, d in (m.get("locales") or {}).items():
        print(f"## {loc}")
        (check_ios if plat == "ios" else check_android)(
            loc, d, errors, warns, *([] if plat == "ios" else [focus]))
        print()

    hist = os.path.join(aso_dir, "rank-history.csv")
    if os.path.exists(hist):
        seen, ever = {}, set()
        with open(hist, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if (r.get("platform") or "ios") != plat:
                    continue
                key = (r["country"], r["keyword"])
                seen[key] = seen.get(key, 0) + 1
                if r["rank"]:
                    ever.add(key)
        dead = [k for k, c in seen.items() if k not in ever and c >= 2]
        if dead:
            print(f"## Keyword chết ({plat}: chưa từng lọt kết quả, đo ≥2 lần)")
            for c, kw in sorted(dead):
                print(f"   {c}/{kw}")
            print("   → thu hồi chỗ cho bản sau\n")

    man = os.path.join(aso_dir, "screenshots", "manifest.yml")
    if os.path.exists(man):
        with open(man, encoding="utf-8") as f:
            sm = yaml.safe_load(f) or {}
        for name, st in (sm.get("sets") or {}).items():
            bad = [s for s in (st.get("slides") or []) if not s.get("ip_cleared")]
            if bad and st.get("ready_for_submission"):
                errors.append(f"screenshots/{name}: {len(bad)} slide chưa clear IP "
                              f"nhưng đã đánh dấu sẵn sàng submit")

    for w in warns:
        print(f"CẢNH BÁO  {w}")
    for e in errors:
        print(f"LỖI       {e}")
    if errors:
        print(f"\nKHÔNG ĐẠT — {len(errors)} lỗi chặn.")
        sys.exit(1)
    print(f"\nĐẠT" + (f" ({len(warns)} cảnh báo)" if warns else ""))


if __name__ == "__main__":
    main()
