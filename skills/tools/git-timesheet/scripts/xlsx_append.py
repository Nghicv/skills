#!/usr/bin/env python3
"""Append effort rows to an .xlsx tracking sheet WITHOUT re-saving the workbook.

Spreadsheet libraries that load-and-save (openpyxl, pandas) silently drop
things they do not understand: Google-Sheets extensions, data validations,
array formulas, charts. This script instead edits only the target sheet's XML
inside the zip; every other part is copied byte-for-byte.

Subcommands
  last-end  print the latest end date already logged for the configured person
  append    write rows (JSON from build_rows.py) after the last used row
  tsv       print rows as tab-separated text in sheet column order (for pasting)

Safety: append refuses to touch a row that already contains any value or
formula, refuses rows that start on/before the person's last logged end date
(unless --allow-overlap), and writes a .bak copy first.
"""
import argparse, datetime as dt, json, os, re, shutil, sys, zipfile
from xml.sax.saxutils import escape

NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

def col_num(c):
    n = 0
    for ch in c:
        n = n * 26 + ord(ch) - 64
    return n

def split_ref(ref):
    m = re.match(r"([A-Z]+)(\d+)$", ref)
    return m.group(1), int(m.group(2))

class Book:
    def __init__(self, path, sheet_name):
        self.path = path
        self.z = zipfile.ZipFile(path)
        wb = self.z.read("xl/workbook.xml").decode()
        rels = self.z.read("xl/_rels/workbook.xml.rels").decode()
        m = re.search(r'<sheet\b[^>]*\bname="%s"[^>]*/>' % re.escape(escape(sheet_name, {'"': "&quot;"})), wb)
        if not m:
            sys.exit(f"sheet '{sheet_name}' not found")
        rid = re.search(r'r:id="([^"]+)"', m.group(0)).group(1)
        target = re.search(r'<Relationship\b[^>]*Id="%s"[^>]*Target="([^"]+)"' % rid, rels) \
            or re.search(r'<Relationship\b[^>]*Target="([^"]+)"[^>]*Id="%s"' % rid, rels)
        t = target.group(1).lstrip("/")
        self.sheet_path = t if t.startswith("xl/") else "xl/" + t
        self.date1904 = 'date1904="1"' in wb or "date1904=\"true\"" in wb
        self.xml = self.z.read(self.sheet_path).decode()
        self.shared = []
        if "xl/sharedStrings.xml" in self.z.namelist():
            ss = self.z.read("xl/sharedStrings.xml").decode()
            self.shared = [unescape_xml("".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S)))
                           for si in re.findall(r"<si>(.*?)</si>", ss, re.S)]

    def rows(self):
        """Yield (row_number, row_xml) for every <row> element."""
        for m in re.finditer(r'<row\b[^>]*\br="(\d+)"[^>]*?(?:/>|>.*?</row>)', self.xml, re.S):
            yield int(m.group(1)), m.group(0)

    def cell_values(self, row_xml):
        out = {}
        for m in re.finditer(r'<c\b([^>]*?)(?:/>|>(.*?)</c>)', row_xml, re.S):
            attrs, body = m.group(1), m.group(2) or ""
            col, _ = split_ref(re.search(r'r="([A-Z]+\d+)"', attrs).group(1))
            t = re.search(r'\bt="(\w+)"', attrs)
            t = t.group(1) if t else "n"
            v = re.search(r"<v>(.*?)</v>", body, re.S)
            if t == "s" and v:
                out[col] = self.shared[int(v.group(1))]
            elif t == "inlineStr":
                out[col] = unescape_xml("".join(re.findall(r"<t[^>]*>(.*?)</t>", body, re.S)))
            elif v:
                out[col] = unescape_xml(v.group(1)) if t == "str" else float(v.group(1))
            elif "<f" in body:
                out[col] = "=formula"
        return out

    def to_date(self, v):
        if isinstance(v, float):
            return (dt.date(1904, 1, 1) if self.date1904 else dt.date(1899, 12, 30)) + dt.timedelta(days=int(v))
        if isinstance(v, str):
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                try:
                    return dt.datetime.strptime(v.strip(), fmt).date()
                except ValueError:
                    pass
        return None

    def serial(self, iso):
        base = dt.date(1904, 1, 1) if self.date1904 else dt.date(1899, 12, 30)
        return (dt.date.fromisoformat(iso) - base).days

def unescape_xml(s):
    return (s.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
             .replace("&apos;", "'").replace("&amp;", "&"))

def last_end(book, sc):
    cols, person = sc["columns"], sc["person"]
    best, style_row = None, None
    for n, rx in book.rows():
        if n < sc.get("first_data_row", 2):
            continue
        v = book.cell_values(rx)
        if v.get(cols["person"]) != person:
            continue
        d = book.to_date(v.get(cols["end"]))
        if d and (best is None or d > best):
            best = d
        style_row = n
    return best, style_row

def styles_of(book, row_no):
    for n, rx in book.rows():
        if n == row_no:
            return {split_ref(re.search(r'r="([A-Z]+\d+)"', m.group(1)).group(1))[0]:
                    (re.search(r'\bs="(\d+)"', m.group(1)) or [None, None])[1]
                    for m in re.finditer(r"<c\b([^>]*?)(?:/>|>)", rx)}
    return {}

def cmd_append(book, sc, rows, a):
    cols = sc["columns"]
    last, my_last_row = last_end(book, sc)
    if last and not a.allow_overlap:
        bad = [r for r in rows if dt.date.fromisoformat(r["start"]) <= last]
        if bad:
            sys.exit(f"refusing: {len(bad)} row(s) start on/before last logged end {last} "
                     f"(first: {bad[0]['start']}). Rebuild rows with --since {last + dt.timedelta(1)}.")
    used = [n for n, rx in book.rows() if re.search(r"<v>|<is>|<f[ >]", rx)]
    first = max(max(used) + 1, sc.get("append_from_row", 0))
    style_src = sc.get("style_row") or my_last_row
    style = styles_of(book, style_src) if style_src else {}
    existing = dict(book.rows())
    xml = book.xml
    for i, r in enumerate(rows):
        R = first + i
        old = existing.get(R)
        cells = {}
        if old:
            if re.search(r"<v>|<is>|<f[ >]", old):
                sys.exit(f"row {R} is not empty; aborting")
            for m in re.finditer(r'<c\b[^>]*?(?:/>|>.*?</c>)', old, re.S):
                cells[split_ref(re.search(r'r="([A-Z]+\d+)"', m.group(0)).group(1))[0]] = m.group(0)
        values = dict(r)
        values["person"], values["role"] = sc["person"], sc.get("role", "")
        for field, col in cols.items():
            if field not in values or values[field] in (None, ""):
                continue
            s = style.get(col) or (re.search(r'\bs="(\d+)"', cells.get(col, "")) or [None, None])[1]
            sa = f' s="{s}"' if s else ""
            val = values[field]
            if field in ("start", "end"):
                cells[col] = f'<c r="{col}{R}"{sa}><v>{book.serial(val)}</v></c>'
            elif isinstance(val, (int, float)):
                cells[col] = f'<c r="{col}{R}"{sa}><v>{val}</v></c>'
            else:
                cells[col] = f'<c r="{col}{R}"{sa} t="inlineStr"><is><t>{escape(str(val))}</t></is></c>'
        body = "".join(cells[c] for c in sorted(cells, key=col_num))
        attrs = re.match(r"<row\b([^>]*?)/?>", old).group(1) if old else f' r="{R}"'
        attrs = re.sub(r'\s(hidden|outlineLevel|collapsed)="[^"]*"', "", attrs)
        new = f"<row{attrs}>{body}</row>"
        if old:
            xml = xml.replace(old, new, 1)
        else:
            nxt = next((m for m in re.finditer(r'<row\b[^>]*\br="(\d+)"', xml) if int(m.group(1)) > R), None)
            pos = nxt.start() if nxt else xml.index("</sheetData>")
            xml = xml[:pos] + new + xml[pos:]
    print(f"{'would write' if a.dry_run else 'wrote'} {len(rows)} rows at {first}-{first + len(rows) - 1}"
          f" (styles from row {style_src})")
    if a.dry_run:
        return
    bak = book.path + ".bak"
    shutil.copy2(book.path, bak)
    tmp = book.path + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
        for it in book.z.infolist():
            data = xml.encode() if it.filename == book.sheet_path else book.z.read(it.filename)
            out.writestr(it, data)
    book.z.close()
    shutil.move(tmp, book.path)
    print(f"backup: {bak}")

def cmd_tsv(sc, rows):
    cols = sc["columns"]
    width = max(col_num(c) for c in cols.values())
    for r in rows:
        values = dict(r, person=sc["person"], role=sc.get("role", ""))
        line = [""] * width
        for field, col in cols.items():
            v = values.get(field, "")
            if field in ("start", "end") and v:
                v = dt.date.fromisoformat(v).strftime(sc.get("tsv_date_format", "%d/%m/%Y"))
            line[col_num(col) - 1] = str(v)
        print("\t".join(line))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["last-end", "append", "tsv"])
    ap.add_argument("--config", required=True)
    ap.add_argument("--rows")
    ap.add_argument("--file", help="override sheet.file from config")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--allow-overlap", action="store_true")
    a = ap.parse_args()
    sc = json.load(open(a.config))["sheet"]
    rows = json.load(open(a.rows)) if a.rows else []
    if a.cmd == "tsv":
        return cmd_tsv(sc, rows)
    book = Book(os.path.expanduser(a.file or sc["file"]), sc["name"])
    if a.cmd == "last-end":
        d, row = last_end(book, sc)
        print(f"{d.isoformat() if d else 'none'}\t(last row for person: {row})")
    else:
        cmd_append(book, sc, rows, a)

if __name__ == "__main__":
    main()
