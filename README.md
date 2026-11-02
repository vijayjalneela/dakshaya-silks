# Dakshaya Boutique website

Public storefront for Dakshaya Boutique. Static site served by GitHub Pages.

- `index.html` – the page. Shop settings (WhatsApp number, address) are at the top of the script.
- `descriptions.json` – display names, descriptions and "best for" per item code (kept separately so a new catalog export does not wipe them).
- `catalog.json` – in-stock items exported from the shop book app. Selling prices only; no cost data.
- `img/` – item photos (`<code>.jpg` large, `<code>-s.jpg` small).

To refresh the collection, export again from the shop book and replace `catalog.json` and `img/`.

## Photo enhancement
Product photos are gently enhanced (brightness/contrast on luminance only, so colours stay true; mild saturation, clarity and sharpening).
After replacing `img/` with a new export, run: `python3 tools/enhance.py img img` (needs Pillow and numpy). Run it once per export only — running it twice enhances twice.
