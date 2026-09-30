import csv
import os
from PIL import Image, ImageDraw, ImageFont

CSV_PATH = "runs/error_analysis/ghostvision_crabpot_v1_fp_analysis.csv"
IMAGE_DIR = "data/derived/ghostvision_yolo/test/images"
OUT_PATH = "runs/error_analysis/v1_top20_localization_analysis.jpg"

rows = []

with open(CSV_PATH, newline="") as f:
    for row in csv.DictReader(f):
        if row["type"] != "FP":
            continue

        iou = float(row["best_iou"])

        if iou <= 0:
            continue

        pred_x1 = float(row["pred_x1"])
        pred_y1 = float(row["pred_y1"])
        pred_x2 = float(row["pred_x2"])
        pred_y2 = float(row["pred_y2"])

        gt_x1 = float(row["gt_x1"])
        gt_y1 = float(row["gt_y1"])
        gt_x2 = float(row["gt_x2"])
        gt_y2 = float(row["gt_y2"])

        pred_w = pred_x2 - pred_x1
        pred_h = pred_y2 - pred_y1
        gt_w = gt_x2 - gt_x1
        gt_h = gt_y2 - gt_y1

        rows.append({
            "image": row["image"],
            "confidence": float(row["confidence"]),
            "iou": iou,
            "pred": (pred_x1, pred_y1, pred_x2, pred_y2),
            "gt": (gt_x1, gt_y1, gt_x2, gt_y2),
            "width_ratio": pred_w / gt_w if gt_w else 0,
            "height_ratio": pred_h / gt_h if gt_h else 0,
        })

rows.sort(
    key=lambda r: (r["iou"], -r["confidence"]),
    reverse=True
)

rows = rows[:20]

tile_w = 640
tile_h = 700
cols = 2
rows_count = 10

sheet = Image.new(
    "RGB",
    (tile_w * cols, tile_h * rows_count),
    "white"
)

draw = ImageDraw.Draw(sheet)

try:
    font = ImageFont.truetype("arial.ttf", 18)
    small_font = ImageFont.truetype("arial.ttf", 15)
except:
    font = ImageFont.load_default()
    small_font = font

for index, item in enumerate(rows):
    image_path = os.path.join(IMAGE_DIR, item["image"])

    if not os.path.exists(image_path):
        print("Missing:", image_path)
        continue

    image = Image.open(image_path).convert("RGB")
    image = image.resize((640, 640))

    tile_x = (index % cols) * tile_w
    tile_y = (index // cols) * tile_h

    sheet.paste(image, (tile_x, tile_y))

    pred = item["pred"]
    gt = item["gt"]

    # GT = blue
    draw.rectangle(
        gt,
        outline="blue",
        width=4
    )

    # Prediction = red
    draw.rectangle(
        pred,
        outline="red",
        width=4
    )

    text = (
        f"#{index + 1}  "
        f"conf={item['confidence']:.3f}  "
        f"IoU={item['iou']:.3f}\n"
        f"Pred/GT W={item['width_ratio']:.2f}  "
        f"H={item['height_ratio']:.2f}"
    )

    draw.rectangle(
        (tile_x + 5, tile_y + 5, tile_x + 635, tile_y + 55),
        fill="white"
    )

    draw.multiline_text(
        (tile_x + 10, tile_y + 8),
        text,
        fill="black",
        font=small_font,
        spacing=2
    )

sheet.save(OUT_PATH, quality=95)

print("Generated:", OUT_PATH)
print("Samples:", len(rows))
print()
print("Legend:")
print("BLUE = ground truth")
print("RED  = model prediction")
