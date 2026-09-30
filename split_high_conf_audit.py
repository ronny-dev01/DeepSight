from pathlib import Path
from PIL import Image, ImageDraw
import re

src = Path("runs/error_analysis/v1_high_conf_fp_vs_tp.jpg")
out_dir = Path("runs/error_analysis/high_conf_sheets")
out_dir.mkdir(parents=True, exist_ok=True)

img = Image.open(src).convert("RGB")

# Original audit was created as:
# 640 px wide, 365 px per pair-row.
row_h = 365
rows = img.height // row_h

print(f"Source size: {img.size}")
print(f"Detected rows: {rows}")

for start in range(0, rows, 6):
    end = min(start + 6, rows)

    crop = img.crop(
        (0, start * row_h, 640, end * row_h)
    )

    number = start // 6 + 1
    path = out_dir / f"sheet_{number}.jpg"

    crop.save(path, quality=95)

    print(path)

print("Done.")
