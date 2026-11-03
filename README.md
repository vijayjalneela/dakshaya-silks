# Dakshaya Boutique website

Public storefront for Dakshaya Boutique. Static site served by Cloudflare Pages (deploys automatically from this repo).

- `index.html` – the page. Shop settings (WhatsApp number, address) are at the top of the script.
- `descriptions.json` – display names, descriptions and "best for" per item code (kept separately so a new catalog export does not wipe them).
- `catalog.json` – items exported from the shop book app, including sold-out ones (stock 0), which show in the "Sold out" section with a restock request. Selling prices only; no cost data.
- `img/` – item photos (`<code>.jpg` large, `<code>-s.jpg` small).

To refresh the collection, export again from the shop book, replace `catalog.json`, put the exported photos in `photos-raw/`, then run the photo enhancement below.

## Photo enhancement
Product photos are gently enhanced (brightness/contrast on luminance only, so colours stay true; mild saturation, clarity and sharpening).
Run: `python3 tools/enhance.py photos-raw img` (needs Pillow and numpy). It reads the original photos from `photos-raw/` and writes enhanced large and small versions into `img/`, so running it again never enhances a photo twice. It works for every item code (sarees, kurtis, jewellery …). To redo only some items: `python3 tools/enhance.py photos-raw img ds-014 kt-003`.

## Other files
- `_headers` – security and caching headers that Cloudflare Pages adds to every response.
- `robots.txt`, `sitemap.xml` – help search engines find the site.
- `img/icon-180.png` – the icon shown when someone adds the site to their phone's home screen.

## Face of the Day
Customers send a photo with their first name, occasion, saree code and what they loved, on WhatsApp, with permission to show it.
To feature one: put the photo in `img/faces/` (e.g. `lakshmi-2026-11-05.jpg`) and add an entry to `faces.json`:
`{"img":"lakshmi-2026-11-05.jpg","name":"Lakshmi","occasion":"her sister's wedding","code":"DS-002","review":"Their words, as written","date":"2026-11-05"}`
The entry for today shows; otherwise the most recent earlier one. Older entries appear under "Our happy customers". Entries dated in the future wait until their day. To remove a photo, delete its entry and file.

## Sunday launches and the weekly update
- In the shop book, every item has a "Launch on website" date (new items default to the coming Sunday).
- The website hides an item until 10:00 AM India time on its launch date, then shows it in New arrivals. The ribbon shows the next launch date.
- A daily scheduled task prepares an update from the shop book on the `pending-sync` branch (preview: add `?preview` to the preview link to see queued pieces) and publishes it to `main` only after the owner approves; on Saturdays it asks for approval of Sunday's launch by 5 PM: new items with their photos, stock, prices and offers. Run by hand the same way:
  1. Save the shop book's `sarees` collection as JSON files into a folder (ArtifactData `list`, `out_dir`).
  2. `python3 -I tools/sync_catalog.py plan <folder>` lists photos to download (shop book asset ids).
  3. Download each listed photo as `<asset>.jpg` into a photos folder (Artifact `read` with `path` = asset id).
  4. `python3 -I tools/sync_catalog.py build <folder> <photos folder>`, then commit and push.
- `img/.photos.json` remembers which shop-book photo each website image came from, so only new or changed photos are downloaded.
