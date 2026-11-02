"""Gentle, colour-true photo enhancement for Dakshaya product photos.
Brightness/contrast are stretched on luminance only (hue is never shifted),
then a mild saturation lift and sharpening. Writes large + small versions."""
import sys, glob, os
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import numpy as np

def enhance(im):
    im = ImageOps.exif_transpose(im).convert("RGB")
    ycc = np.asarray(im.convert("YCbCr")).astype(np.float32)
    y = ycc[..., 0]
    lo, hi = np.percentile(y, 0.7), np.percentile(y, 99.5)
    if hi - lo > 40:
        y = (y - lo) / (hi - lo) * 245 + 5
    # soft S-curve for depth
    t = np.clip(y / 255, 0, 1)
    y = 255 * (t + 0.18 * (t - 0.5) * (1 - abs(2 * t - 1)) * 2 * 0.5)
    # lift midtones slightly if the photo is dark
    m = y.mean()
    if m < 115:
        g = np.log(m / 255) / np.log(0.45)  # gamma that moves the mean toward ~115
        y = 255 * np.clip(y / 255, 0, 1) ** min(1.0, max(0.75, 1 / g))
    ycc[..., 0] = np.clip(y, 0, 255)
    im = Image.fromarray(ycc.astype(np.uint8), "YCbCr").convert("RGB")
    im = im.filter(ImageFilter.UnsharpMask(radius=24, percent=22, threshold=0))  # clarity: local contrast brings out the weave
    im = ImageEnhance.Color(im).enhance(1.16)
    im = im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=2))
    return im

def save(im, base):
    im.save(base + ".jpg", quality=80, optimize=True, progressive=True)
    sm = im.copy(); sm.thumbnail((480, 600), Image.LANCZOS)
    sm.save(base + "-s.jpg", quality=72, optimize=True, progressive=True)

if __name__ == "__main__":
    src_dir, out_dir = sys.argv[1], sys.argv[2]
    codes = sys.argv[3:]
    files = [f for f in sorted(glob.glob(os.path.join(src_dir, "*.jpg"))) if os.path.basename(f).startswith("ds-") and not f.endswith("-s.jpg")]
    if codes: files = [f for f in files if os.path.basename(f)[:-4] in codes]
    os.makedirs(out_dir, exist_ok=True)
    for f in files:
        save(enhance(Image.open(f)), os.path.join(out_dir, os.path.basename(f)[:-4]))
    print(len(files), "done")
