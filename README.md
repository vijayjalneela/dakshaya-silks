# Dakshaya Boutique website

Public storefront for Dakshaya Boutique. Static site served by Cloudflare Pages (deploys automatically from this repo).

- `index.html` – the page. Shop settings (WhatsApp number, address) are at the top of the script.
- `descriptions.json` – display names, descriptions and "best for" per item code (kept separately so a new catalog export does not wipe them).
- `catalog.json` – in-stock items exported from the shop book app. Selling prices only; no cost data.
- `img/` – item photos (`<code>.jpg` large, `<code>-s.jpg` small).

To refresh the collection, export again from the shop book, replace `catalog.json`, put the exported photos in `photos-raw/`, then run the photo enhancement below.

## Photo enhancement
Product photos are gently enhanced (brightness/contrast on luminance only, so colours stay true; mild saturation, clarity and sharpening).
Run: `python3 tools/enhance.py photos-raw img` (needs Pillow and numpy). It reads the original photos from `photos-raw/` and writes enhanced large and small versions into `img/`, so running it again never enhances a photo twice. It works for every item code (sarees, kurtis, jewellery …). To redo only some items: `python3 tools/enhance.py photos-raw img ds-014 kt-003`.

## Other files
- `_headers` – security and caching headers that Cloudflare Pages adds to every response.
- `robots.txt`, `sitemap.xml` – help search engines find the site.
- `img/icon-180.png` – the icon shown when someone adds the site to their phone's home screen.
