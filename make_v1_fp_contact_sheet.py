from pathlib import Path
import csv
from PIL import Image, ImageDraw, ImageFont

CSV_PATH = Path("runs/error_analysis/ghostvision_crabpot_v1_fp_analysis.csv")
IMAGE_ROOT = Path("data/derived/ghostvision_yolo/test/images")
OUT = Path("runs/error_analysis/v1_top20_fp_contact_sheet.jpg")

rows = []

with CSV_PATH.open(newline="") as f:
    for row in csv.DictReader(f):
        if row["type"] == "FP":
            rows.append(row)

rows.sort(key=lambda r: float(r["confidence"]), reverse=True)
rows = rows[:20]

thumb_w = 320
thumb_h = 320
label_h = 58
cols = 4
rows_count = 5

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

        offset_x = paste_x
        offset_y = paste_y

        def box(values):
            return (
                offset_x + float(values[0]) * scale,
                offset_y + float(values[1]) * scale,
                offset_x + float(values[2]) * scale,
                offset_y + float(values[3]) * scale,
            )

        pred_box = box((
            row["pred_x1"],
            row["pred_y1"],
            row["pred_x2"],
            row["pred_y2"],
        ))

        draw.rectangle(pred_box, outline="red", width=3)

        if row["gt_x1"]:
            gt_box = box((
                row["gt_x1"],
                row["gt_y1"],
                row["gt_x2"],
                row["gt_y2"],
            ))

            draw.rectangle(gt_box, outline="blue", width=3)

    text = (
        f"#{i+1} conf={float(row['confidence']):.3f} "
        f"IoU={float(row['best_iou']):.3f}"
    )

    draw.text(
        (x + 5, y + thumb_h + 5),
        text,
        fill="black",
    )

    draw.text(
        (x + 5, y + thumb_h + 25),
        row["image"][:42],
        fill="black",
    )

sheet.save(OUT, quality=95)

print(f"Created: {OUT}")
