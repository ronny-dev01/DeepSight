from pathlib import Path
import csv
from PIL import Image, ImageDraw

CSV_PATH = Path("runs/error_analysis/ghostvision_crabpot_v1_fp_analysis.csv")
IMAGE_ROOT = Path("data/derived/ghostvision_yolo/test/images")
OUT = Path("runs/error_analysis/v1_high_conf_background_fp_crops.jpg")

rows = []

with CSV_PATH.open(newline="") as f:
    for row in csv.DictReader(f):
        if row["type"] != "FP":
            continue

        if float(row["best_iou"]) != 0.0:
            continue

        if float(row["confidence"]) < 0.30:
            continue

        rows.append(row)

rows.sort(key=lambda r: float(r["confidence"]), reverse=True)

crop_size = 320
label_h = 55
cols = 4
rows_count = (len(rows) + cols - 1) // cols

sheet = Image.new(
    "RGB",
    (cols * crop_size, rows_count * (crop_size + label_h)),
    "white",
)

draw = ImageDraw.Draw(sheet)

for i, row in enumerate(rows):
    path = IMAGE_ROOT / row["image"]

    with Image.open(path).convert("RGB") as im:
        w, h = im.size

        x1 = float(row["pred_x1"])
        y1 = float(row["pred_y1"])
        x2 = float(row["pred_x2"])
        y2 = float(row["pred_y2"])

        bw = x2 - x1
        bh = y2 - y1

        # 3x prediction box context
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2

        half_w = max(bw * 1.5, 40)
        half_h = max(bh * 1.5, 40)

        left = max(0, int(cx - half_w))
        top = max(0, int(cy - half_h))
        right = min(w, int(cx + half_w))
        bottom = min(h, int(cy + half_h))

        crop = im.crop((left, top, right, bottom))
        crop = crop.resize((crop_size, crop_size))

        cell_x = (i % cols) * crop_size
        cell_y = (i // cols) * (crop_size + label_h)

        sheet.paste(crop, (cell_x, cell_y))

        # Red box in crop coordinates
        crop_w = right - left
        crop_h = bottom - top

        sx = crop_size / crop_w
        sy = crop_size / crop_h

        rx1 = (x1 - left) * sx
        ry1 = (y1 - top) * sy
        rx2 = (x2 - left) * sx
        ry2 = (y2 - top) * sy

        draw.rectangle(
            (
                cell_x + rx1,
                cell_y + ry1,
                cell_x + rx2,
                cell_y + ry2,
            ),
            outline="red",
            width=4,
        )

    draw.text(
        (cell_x + 5, cell_y + crop_size + 5),
        f"#{i+1}  conf={float(row['confidence']):.3f}",
        fill="black",
    )

    draw.text(
        (cell_x + 5, cell_y + crop_size + 25),
        row["image"][:42],
        fill="black",
    )

sheet.save(OUT, quality=95)

print(f"Hard-negative crops: {len(rows)}")
print(f"Created: {OUT}")
