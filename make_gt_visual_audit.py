import csv
import os
from PIL import Image, ImageDraw, ImageFont

CSV_PATH = "runs/error_analysis/gt_annotation_consistency.csv"
IMAGE_DIR = "data/derived/ghostvision_yolo/test/images"
OUT_PATH = "runs/error_analysis/gt_annotation_visual_audit.jpg"

with open(CSV_PATH, newline="") as f:
    data = list(csv.DictReader(f))

# Lowest bright-core occupancy = broadest low-intensity annotations.
lowest = sorted(
    data,
    key=lambda r: float(r["bright_core_fraction"])
)[:9]

# Highest contrast = clearest target/context separation.
highest = sorted(
    data,
    key=lambda r: float(r["intensity_contrast_ratio"]),
    reverse=True
)[:9]

selected = []

for r in lowest:
    r = dict(r)
    r["group"] = "LOW BRIGHT-CORE"
    selected.append(r)

for r in highest:
    r = dict(r)
    r["group"] = "HIGH CONTRAST"
    selected.append(r)

tile_w = 620
tile_h = 470
cols = 3
rows = 6

sheet = Image.new(
    "RGB",
    (tile_w * cols, tile_h * rows),
    "white"
)

draw = ImageDraw.Draw(sheet)

try:
    font = ImageFont.truetype("arial.ttf", 17)
    small_font = ImageFont.truetype("arial.ttf", 14)
except:
    font = ImageFont.load_default()
    small_font = font

for index, item in enumerate(selected):

    image_path = os.path.join(
        IMAGE_DIR,
        item["image"]
    )

    if not os.path.exists(image_path):
        continue

    image = Image.open(image_path).convert("RGB")

    w, h = image.size

    cx = float(item["cx_px"])
    cy = float(item["cy_px"])
    bw = float(item["width_px"])
    bh = float(item["height_px"])

    x1 = cx - bw / 2
    y1 = cy - bh / 2
    x2 = cx + bw / 2
    y2 = cy + bh / 2

    # Large contextual crop.
    margin_x = max(bw * 2.0, 100)
    margin_y = max(bh * 2.0, 100)

    crop_x1 = max(0, int(x1 - margin_x))
    crop_y1 = max(0, int(y1 - margin_y))
    crop_x2 = min(w, int(x2 + margin_x))
    crop_y2 = min(h, int(y2 + margin_y))

    crop = image.crop(
        (crop_x1, crop_y1, crop_x2, crop_y2)
    )

    available_w = tile_w - 20
    available_h = tile_h - 90

    scale = min(
        available_w / crop.width,
        available_h / crop.height
    )

    new_w = max(1, int(crop.width * scale))
    new_h = max(1, int(crop.height * scale))

    crop = crop.resize((new_w, new_h))

    box = (
        (x1 - crop_x1) * scale,
        (y1 - crop_y1) * scale,
        (x2 - crop_x1) * scale,
        (y2 - crop_y1) * scale,
    )

    tile_x = (index % cols) * tile_w
    tile_y = (index // cols) * tile_h

    image_x = tile_x + (tile_w - new_w) // 2
    image_y = tile_y + 72

    sheet.paste(
        crop,
        (image_x, image_y)
    )

    box_draw = (
        box[0] + image_x,
        box[1] + image_y,
        box[2] + image_x,
        box[3] + image_y,
    )

    # GT annotation = blue.
    draw.rectangle(
        box_draw,
        outline="blue",
        width=5
    )

    header = (
        f"#{index + 1}  {item['group']}"
    )

    metrics = (
        f"bright={float(item['bright_core_fraction']):.3f}  "
        f"contrast={float(item['intensity_contrast_ratio']):.3f}"
    )

    geometry = (
        f"W={float(item['width_norm']):.3f}  "
        f"H={float(item['height_norm']):.3f}  "
        f"AR={float(item['aspect_ratio']):.2f}"
    )

    draw.rectangle(
        (
            tile_x + 5,
            tile_y + 5,
            tile_x + tile_w - 5,
            tile_y + 65
        ),
        fill="white"
    )

    draw.text(
        (tile_x + 10, tile_y + 8),
        header,
        fill="black",
        font=font
    )

    draw.text(
        (tile_x + 10, tile_y + 31),
        metrics,
        fill="black",
        font=small_font
    )

    draw.text(
        (tile_x + 10, tile_y + 49),
        geometry,
        fill="black",
        font=small_font
    )

sheet.save(
    OUT_PATH,
    quality=95
)

print("Generated:", OUT_PATH)
print("Cases:", len(selected))
print()
print("Rows 1-9  = lowest bright-core occupancy")
print("Rows 10-18 = highest intensity contrast")
print("BLUE = ground-truth annotation")
