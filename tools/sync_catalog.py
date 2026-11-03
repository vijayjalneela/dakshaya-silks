"""Rebuild the website catalog from the Dakshaya Sales shop book.

Used by the weekly automatic update (and by hand). Two steps:

  1. python3 -I tools/sync_catalog.py plan  <docs_dir>
       docs_dir = folder of the shop book's "sarees" documents, one JSON file each
       (ArtifactData list ... out_dir). Prints JSON: the photos to download,
       as [{"code","img","asset"}], i.e. new items or items whose photo changed.

  2. python3 -I tools/sync_catalog.py build <docs_dir> <photos_dir>
       photos_dir = folder holding the downloaded photos named <asset>.jpg/.png/.webp.
       Enhances those photos into img/, then rewrites catalog.json, adds a display
       title to descriptions.json for any new code, and updates img/.photos.json.
       Prints a summary of what changed.

Items keep their "launch" date (YYYY-MM-DD). The website hides an item until
5:00 AM India time on that date, so new pieces can be synced any time before.
Cost price and supplier never leave the shop book.
"""
import sys, os, json, glob, re, shutil, tempfile, subprocess
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "img")
MANIFEST = os.path.join(IMG, ".photos.json")
IST = timezone(timedelta(hours=5, minutes=30))


def load_docs(d):
    out = []
    for f in sorted(glob.glob(os.path.join(d, "**", "*.json"), recursive=True)):
        try:
            x = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        x = x.get("data", x) if isinstance(x, dict) else None
        if isinstance(x, dict) and x.get("code"):
            out.append(x)
    return out


def img_name(code):
    return str(code).split(" ")[0].lower()


def usable(x):
    return (not x.get("sample")) and x.get("photo") and float(x.get("sp") or 0) > 0 \
        and re.match(r"^[A-Z]{1,5}-\d+", str(x.get("code", "")))


def manifest():
    try:
        return json.load(open(MANIFEST))
    except Exception:
        return {}


def plan(docs_dir):
    m = manifest()
    need = []
    for x in load_docs(docs_dir):
        if not usable(x):
            continue
        img = img_name(x["code"])
        have = os.path.exists(os.path.join(IMG, img + ".jpg")) and os.path.exists(os.path.join(IMG, img + "-s.jpg"))
        if not have or m.get(img) != x["photo"]:
            need.append({"code": x["code"], "img": img, "asset": x["photo"]})
    print(json.dumps(need, indent=1))


FIX = {"banarasi silk": "Banarasi Silk", "tussar silk": "Tussar Silk", "mysore crepe": "Mysore Crepe",
       "kanjivaram silk": "Kanjivaram Silk", "soft silk": "Soft Silk", "chicken kari": "Chikankari",
       "cotton lenin handloom": "Cotton Linen Handloom"}


def title_for(x):
    t = str(x.get("type") or "").strip()
    t = FIX.get(t.lower(), t.title() if t.islower() else t)
    cat = x.get("category") or "Saree"
    noun = "Saree" if cat == "Saree" else ("" if cat.lower() in t.lower() else cat)
    words = [w for w in str(x.get("name") or "").split() if w.lower() not in t.lower().split()]
    title = re.sub(r"\s+", " ", " ".join(words + [t, noun])).strip()
    if x.get("fabric") == "Zari Border":
        title += " with Zari Border"
    return title


def build(docs_dir, photos_dir):
    docs = load_docs(docs_dir)
    m = manifest()
    # 1. photos: enhance any downloaded photo into img/
    got = {}
    for f in glob.glob(os.path.join(photos_dir, "*")):
        base = os.path.splitext(os.path.basename(f))[0]
        got[base] = f
    staged = tempfile.mkdtemp()
    todo = []
    for x in docs:
        if not usable(x):
            continue
        img = img_name(x["code"])
        if x["photo"] in got and (m.get(img) != x["photo"] or not os.path.exists(os.path.join(IMG, img + ".jpg"))):
            from PIL import Image
            im = Image.open(got[x["photo"]]); im.verify()
            Image.open(got[x["photo"]]).convert("RGB").save(os.path.join(staged, img + ".jpg"), quality=95)
            todo.append((img, x["photo"]))
    if todo:
        subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "enhance.py"), staged, IMG], check=True)
        for img, asset in todo:
            m[img] = asset
    shutil.rmtree(staged, ignore_errors=True)
    # 2. catalog
    old = json.load(open(os.path.join(ROOT, "catalog.json"), encoding="utf-8"))
    old_codes = {i["code"] for i in old.get("items", [])}
    items, missing = [], []
    for x in sorted(docs, key=lambda d: d.get("addedAt", 0)):
        if not usable(x):
            continue
        img = img_name(x["code"])
        if not os.path.exists(os.path.join(IMG, img + "-s.jpg")):
            missing.append(x["code"]); continue
        items.append({"code": x["code"], "category": x.get("category") or "Saree", "name": re.sub(r"\s+", " ", str(x.get("name", ""))).strip(),
                      "type": x.get("type", ""), "material": x.get("material", ""), "size": x.get("size", ""),
                      "border": x.get("fabric", ""), "color": x.get("color", ""), "blouse": bool(x.get("blouse")),
                      "dupatta": bool(x.get("dupatta")), "length": x.get("length", ""), "price": x.get("sp"),
                      "stock": int(x.get("stock") or 0), "img": img, "added": x.get("addedAt", 0),
                      "disc": x.get("disc") or 0, "clearance": bool(x.get("clearance")), "offerEnds": x.get("offerEnds", ""),
                      **({"launch": x["launch"]} if re.match(r"^\d{4}-\d{2}-\d{2}$", str(x.get("launch") or "")) else {})})
    cat = {"updated": datetime.now(IST).strftime("%Y-%m-%d"), "items": items}
    json.dump(cat, open(os.path.join(ROOT, "catalog.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    # 3. titles for new codes (curated ones are never overwritten)
    dpath = os.path.join(ROOT, "descriptions.json")
    desc = json.load(open(dpath, encoding="utf-8"))
    titled = []
    for i in items:
        c = i["code"].split(" ")[0]
        if c not in desc:
            src = next(d for d in docs if d["code"] == i["code"])
            desc[c] = {"title": title_for(src)}; titled.append(c)
    open(dpath, "w", encoding="utf-8").write(json.dumps(desc, ensure_ascii=False, indent=1))
    json.dump(m, open(MANIFEST, "w"), indent=0, sort_keys=True)
    # 4. summary
    now = datetime.now(IST).strftime("%Y-%m-%d")
    new_codes = [i["code"] for i in items if i["code"] not in old_codes]
    upcoming = {}
    for i in items:
        if i.get("launch", "") > now or (i.get("launch") == now and datetime.now(IST).hour < 5):
            upcoming.setdefault(i["launch"], []).append(i["code"])
    print(json.dumps({"items": len(items), "in_stock": sum(1 for i in items if i["stock"] > 0),
                      "sold_out": sum(1 for i in items if i["stock"] <= 0), "new_on_site": new_codes,
                      "removed": sorted(old_codes - {i["code"] for i in items}), "photos_updated": [t[0] for t in todo],
                      "titles_added": titled, "waiting_for_launch": upcoming, "skipped_no_photo": missing}, indent=1))


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "plan":
        plan(sys.argv[2])
    elif len(sys.argv) >= 4 and sys.argv[1] == "build":
        build(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
