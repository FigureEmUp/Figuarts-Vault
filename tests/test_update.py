import sys, json; sys.path.insert(0, '.')
import update_catalog as u
html = '''<a href="/item/16086/?wovn=en">S.H.Figuarts ENDEAVOR Retail <em>¥13,200</em>(incl. tax) November 2, 2026 Preorders April 2027 Release</a>
<a href="/item/16154/">Re-Release S.H.Figuarts (SHINKOCCHOU SEIHOU) ULTRAMAN TIGA MULTI TYPE 30th Anniversary Edition Retail ¥15,400 (incl. tax) April 2027 Release</a>
<a href="/item/16214/">S.H.Figuarts SON GOKU &amp; Dragon-DRAGON BALL STORE Exclusive Edition- Other Limited Editions ¥8,800 November 2026 Release</a>
<a href="/item/16144/">[Berserk] “S.H.Figuarts FEMTO” is here! Pre-orders begin</a>
<a href="/item/16086/">S.H.Figuarts ENDEAVOR</a><a href="/about/">About</a>'''
items = u.extract_items(html)
assert set(items) == {"16086", "16154", "16214"}, items
assert items["16086"] == {"name": "ENDEAVOR", "price": "¥13,200", "release": "2027-04", "url": "https://tamashiiweb.com/item/16086/"}, items["16086"]
assert items["16154"]["release"] == "2027-04" and items["16154"]["price"] == "¥15,400"
ex = {"figures": [{"id": "douma", "name": "Douma", "series": "Demon Slayer", "release": "2026-11", "price": "¥11,000"}]}
m = u.merge(ex, {"16164": {"name": "DOMA", "price": "¥11,000", "release": "2026-11", "url": "x"}, **items}, {"16086": "My Hero Academia"})
ids = {f["id"]: f for f in m["figures"]}
assert "douma" in ids and ids["douma"]["tn"] == "16164" and ids["douma"]["series"] == "Demon Slayer", ids   # adopted, id preserved
assert ids["tn16086"]["series"] == "My Hero Academia" and ids["tn16214"]["series"] == "Other"
m2 = u.merge(m, {}, {}); assert len(m2["figures"]) == len(m["figures"])   # idempotent, never deletes
print("all tests passed")
