#!/usr/bin/env python3
"""Updates catalog.json from Tamashii Nations' public listings.
Stdlib only. Polite: honors robots.txt, identifies itself, rate-limits.
Never deletes existing entries; aborts (exit 1) if parsing looks broken."""
import json, re, sys, time, datetime, difflib, urllib.request, urllib.robotparser
from html.parser import HTMLParser

BASE = "https://tamashiiweb.com"
UA = "FiguartsVaultBot/1.0 (hobby catalog; contact: YOUR_EMAIL_HERE)"
DELAY, MAX_REQUESTS, MIN_FOUND = 1.5, 120, 15
LIST_PAGES = ["/item_brand/shfiguarts/", "/item_brand/shinkocchou/", "/item_brand/figuarts_series/"]
MONTHS = {m: i + 1 for i, m in enumerate("January February March April May June July August September October November December".split())}

class Anchors(HTMLParser):
    """Collects (href, visible text) for every <a>."""
    def __init__(self):
        super().__init__(); self.out = []; self._h = None; self._t = []
    def handle_starttag(self, tag, attrs):
        if tag == "a": self._h = dict(attrs).get("href"); self._t = []
    def handle_data(self, d):
        if self._h is not None: self._t.append(d)
    def handle_endtag(self, tag):
        if tag == "a" and self._h is not None:
            self.out.append((self._h, re.sub(r"\s+", " ", " ".join(self._t)).strip())); self._h = None

def anchors(html):
    p = Anchors(); p.feed(html); return p.out

STOP = r"(?:Retail|Tamashii Web Shop|Tamashii Store|TAMASHII STORE|TAMASHII NATION|Other Limited|Other Event|Lottery|Preorders|¥|\d[\d,]*円|\*)"
def parse_item(text):
    """Returns dict(name, price, release) or None. Handles English and Japanese text."""
    m = re.match(r"^(?:Re-Release |Second Shipment |再販 )?S\.H\.Figuarts\s+(.*)$", text)
    if not m: return None
    rest = m.group(1)
    name = re.split(r"\s+" + STOP, rest)[0].strip(" -")
    if not name or len(name) > 90: return None
    price = (re.search(r"¥\s?([\d,]+)", rest) or re.search(r"([\d,]+)円", rest))
    rel = re.search(r"([A-Z][a-z]+) (\d{4}) Release", rest)
    release = ""
    if rel and rel.group(1) in MONTHS: release = f"{rel.group(2)}-{MONTHS[rel.group(1)]:02d}"
    else:
        j = re.search(r"(\d{4})年(\d{1,2})月", rest)
        if j: release = f"{j.group(1)}-{int(j.group(2)):02d}"
    return {"name": name, "price": f"¥{price.group(1)}" if price else "", "release": release}

def extract_items(html):
    found = {}
    for href, text in anchors(html):
        m = re.search(r"/item/(\d+)/?", href)
        if not m: continue
        info = parse_item(text)
        if not info: continue
        cur = found.setdefault(m.group(1), {"name": info["name"], "price": "", "release": "", "url": f"{BASE}/item/{m.group(1)}/"})
        for k in ("price", "release"):
            if info[k] and not cur[k]: cur[k] = info[k]
    return found

def norm(s): return re.sub(r"[^a-z0-9\u3040-\u30ff\u4e00-\u9fff]", "", s.lower())

def merge(existing, scraped, series_map):
    figs = existing.get("figures", [])
    by_tn = {f["tn"]: f for f in figs if f.get("tn")}
    for tn, s in scraped.items():
        f = by_tn.get(tn)
        if not f:  # adopt a hand-seeded entry with the same/similar name so saved user data keeps its id
            for g in figs:
                if not g.get("tn") and difflib.SequenceMatcher(None, norm(g["name"]), norm(s["name"])).ratio() >= 0.85:
                    f = g; break
        if not f:
            f = {"id": f"tn{tn}", "series": ""}; figs.append(f)
        f["tn"], f["url"] = tn, s["url"]
        f["name"] = s["name"]
        for k in ("price", "release"):
            if s[k]: f[k] = s[k]
            else: f.setdefault(k, "")
        f["series"] = series_map.get(tn) or f.get("series") or "Other"
    existing["figures"] = sorted(figs, key=lambda f: (f.get("release") or "0000", f["name"]), reverse=True)
    existing["updated"] = datetime.date.today().isoformat()
    return existing

class Fetcher:
    def __init__(self):
        self.n = 0; self.rp = urllib.robotparser.RobotFileParser(BASE + "/robots.txt")
        try: self.rp.read()
        except Exception: pass
    def get(self, path):
                   sep = "&" if "?" in path else "?"
           url = BASE + path + sep + "wovn=en"
        if self.n >= MAX_REQUESTS or not self.rp.can_fetch(UA, url): return ""
        self.n += 1; time.sleep(DELAY)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"}), timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            print("WARN", path, e, file=sys.stderr); return ""

def series_from_character_pages(fx):
    idx = fx.get("/item_character/")
    chars = {}
    for href, text in anchors(idx):
        m = re.match(r"^(?:https://tamashiiweb\.com)?(/item_character/[\w-]+/)", href)
        if m and text and len(text) < 60 and m.group(1) not in chars: chars[m.group(1)] = text
    out = {}
    for path, label in chars.items():
        for tn in extract_items(fx.get(path)):
            out.setdefault(tn, label)
    return out

def main():
    fx = Fetcher(); scraped = {}
    for p in LIST_PAGES: scraped.update(extract_items(fx.get(p)))
    today = datetime.date.today()
    for i in range(0, 12):  # monthly schedule pages
        y, m = divmod(today.year * 12 + today.month - 1 + i, 12)
        scraped.update(extract_items(fx.get(f"/schedule/?month={y}-{m + 1:02d}")))
    print(f"Found {len(scraped)} figures with {fx.n} requests")
    if len(scraped) < MIN_FOUND:
        print("Too few figures parsed; the site layout may have changed. Not writing.", file=sys.stderr); sys.exit(1)
    series = series_from_character_pages(fx)
    try: existing = json.load(open("catalog.json", encoding="utf-8"))
    except Exception: existing = {"figures": []}
    out = merge(existing, scraped, series)
    json.dump(out, open("catalog.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("Wrote catalog.json with", len(out["figures"]), "figures")

if __name__ == "__main__": main()
