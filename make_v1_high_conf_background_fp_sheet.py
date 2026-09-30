from pathlib import Path
import csv
from PIL import Image, ImageDraw

CSV_PATH = Path("runs/error_analysis/ghostvision_crabpot_v1_fp_analysis.csv")
IMAGE_ROOT = Path("data/derived/ghostvision_yolo/test/images")
OUT = Path("runs/error_analysis/v1_high_conf_background_fp_contact_sheet.jpg")

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

thumb_w = 320
thumb_h = 320
label_h = 58
cols = 4
rows_count = (len(rows) + cols - 1) // cols

sheet = Image.new(
    "RGB",
    (cols * thumb_w, rows_count * (thumb_h + label_h)),
    "white",
)

draw = ImageDraw.Draw(sheet)

for i, row in enumerate(rows):
    path = IMAGE_ROOT / row["image"]

    with Image.open(path).convert("RGB") as im:
        original_w, original_h = im.size
        scale = min(thumb_w / original_w, thumb_h / original_h)

        new_w = int(original_w * scale)
        new_h = int(original_h * scale)

        im = im.resize((new_w, new_h))

        x = (i % cols) * thumb_w
        y = (i // cols) * (thumb_h + label_h)

        paste_x = x + (thumb_w - new_w) // 2
        paste_y = y + (thumb_h - new_h) // 2

        sheet.paste(im, (paste_x, paste_y))

        pred_box = (
            paste_x + float(row["pred_x1"]) * scale,
            paste_y + float(row["pred_y1"]) * scale,
            paste_x + float(row["pred_x2"]) * scale,
            paste_y + float(row["pred_y2"]) * scale,
        )

        draw.rectangle(pred_box, outline="red", width=3)

    draw.text(
        (x + 5, y + thumb_h + 5),
        f"#{i+1}  conf={float(row['confidence']):.3f}",
        fill="black",
    )

    draw.text(
        (x + 5, y + thumb_h + 25),
        row["image"][:42],
        fill="black",
    )

sheet.save(OUT, quality=95)

print(f"Hard negatives: {len(rows)}")
print(f"Created: {OUT}")
