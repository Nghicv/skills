"""Shared helpers for the aso skill scripts."""
import json, os, plistlib, sys, time, urllib.parse, urllib.request

try:
    import yaml
except ImportError:
    sys.exit("Cần PyYAML: pip3 install pyyaml")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "\
     "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"


def load(aso_dir):
    """Trả về (config, keywords, aso_dir tuyệt đối)."""
    aso_dir = os.path.abspath(aso_dir)
    cfg_path = os.path.join(aso_dir, "config.yml")
    if not os.path.exists(cfg_path):
        sys.exit(f"Không thấy {cfg_path}. Chạy init_app.py trước.")
    with open(cfg_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    kw_path = os.path.join(aso_dir, "keywords.yml")
    kws = []
    if os.path.exists(kw_path):
        with open(kw_path, encoding="utf-8") as f:
            kws = yaml.safe_load(f) or []
    return cfg, kws, aso_dir


def _raw(url, headers=None, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def get(url, headers=None, timeout=25):
    return json.loads(_raw(url, headers, timeout).decode("utf-8", "replace"))


def get_plist(url, headers=None, timeout=25):
    """Endpoint hints trả XML plist chứ không phải JSON."""
    return plistlib.loads(_raw(url, headers, timeout))


def search(term, country, limit=200, retries=3):
    """Trả về (danh sách trackId, tổng số kết quả)."""
    url = ("https://itunes.apple.com/search?"
           + urllib.parse.urlencode({"term": term, "country": country,
                                     "entity": "software", "limit": limit}))
    for attempt in range(retries):
        try:
            d = get(url)
            res = d.get("results", [])
            return [str(x.get("trackId")) for x in res], len(res)
        except Exception:
            if attempt == retries - 1:
                return None, None
            time.sleep(2 * (attempt + 1))
    return None, None


def hints(term, storefront_header, retries=2):
    """Gợi ý autocomplete của App Store cho một storefront."""
    url = ("https://search.itunes.apple.com/WebObjects/MZSearchHints.woa/wa/hints?"
           + urllib.parse.urlencode({"q": term, "clientApplication": "Software"}))
    for attempt in range(retries):
        try:
            d = get_plist(url, headers={"X-Apple-Store-Front": storefront_header})
            out = []
            for h in (d.get("hints") or []):
                t = h.get("term")
                if t:
                    out.append(t)
            return out
        except Exception:
            if attempt == retries - 1:
                return []
            time.sleep(2)
    return []


def sf_header(cfg, country):
    s = (cfg.get("storefronts") or {}).get(country)
    if not s:
        sys.exit(f"storefront '{country}' chưa khai trong config.yml")
    return s["sf_header"]
