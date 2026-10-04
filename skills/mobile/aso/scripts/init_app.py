#!/usr/bin/env python3
"""Dựng khung aso/ cho một app mới.

    python3 init_app.py <repo>/aso --adam-id 1234567890 --name "My App"
"""
import argparse, os, shutil, sys

TPL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("aso_dir")
    ap.add_argument("--platform", default="ios",
                    choices=["ios", "android", "both"])
    ap.add_argument("--adam-id", default="0000000000")
    ap.add_argument("--package-name", default="com.example.app")
    ap.add_argument("--name", default="My App")
    a = ap.parse_args()

    d = os.path.abspath(a.aso_dir)
    if os.path.exists(os.path.join(d, "config.yml")):
        sys.exit(f"{d}/config.yml đã tồn tại.")
    for sub in ("metadata", "measure", "research", "screenshots", "reports"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)

    cfg = open(os.path.join(TPL, "config.yml"), encoding="utf-8").read()
    cfg = (cfg.replace('"0000000000"', f'"{a.adam_id}"')
              .replace('"com.example.app"', f'"{a.package_name}"')
              .replace('"My App"', f'"{a.name}"')
              .replace("platform: ios ", f"platform: {a.platform} "))
    open(os.path.join(d, "config.yml"), "w", encoding="utf-8").write(cfg)

    shutil.copy(os.path.join(TPL, "keywords.yml"), os.path.join(d, "keywords.yml"))
    shutil.copy(os.path.join(TPL, "metadata.version.yml"),
                os.path.join(d, "metadata", "v1.0.yml"))
    shutil.copy(os.path.join(TPL, "screenshots-manifest.yml"),
                os.path.join(d, "screenshots", "manifest.yml"))
    open(os.path.join(d, "CHANGELOG.md"), "w", encoding="utf-8").write(
        "# Lịch sử metadata\n\nMỗi mục: đổi gì · vì sao · kết quả đo được.\n"
        "Ghi cả những lần THẤT BẠI và lý do — đó là phần giá trị nhất.\n")

    gi = os.path.join(d, ".gitignore")
    open(gi, "w", encoding="utf-8").write(
        "# Ảnh screenshot không bao giờ vào git — manifest.yml giữ đường dẫn\n"
        "screenshots/**/*.png\nscreenshots/**/*.jpg\nscreenshots/**/*.mp4\n")

    print(f"Đã dựng {d}/")
    print("Tiếp theo:")
    print("  1. điền storefronts trong config.yml")
    print("  2. discover_keywords.py để tìm keyword (app mới)")
    if a.platform in ("android", "both"):
        print("  2b. Android: đọc references/play-indexing.md TRƯỚC khi soạn "
              "metadata — nhiều luật ngược với iOS")
    print("  3. điền metadata/v1.0.yml → validate_metadata.py")
    print("  4. measure_keywords.py TRƯỚC ngày phát hành → set baseline trong config.yml")


if __name__ == "__main__":
    main()
