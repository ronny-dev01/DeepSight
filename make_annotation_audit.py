import csv
import os
from PIL import Image, ImageDraw, ImageFont

CSV_PATH = "runs/error_analysis/ghostvision_crabpot_v1_fp_analysis.csv"
IMAGE_DIR = "data/derived/ghostvision_yolo/test/images"
OUT_PATH = "runs/error_analysis/v1_annotation_audit_crops.jpg"

candidates = []

with open(CSV_PATH, newline="") as f:
    for row in csv.DictReader(f):
        if row["type"] != "FP":
            continue

        iou = float(row["best_iou"])

        if iou <= 0:
            continue

        pred = tuple(float(row[k]) for k in ["pred_x1", "pred_y1", "pred_x2", "pred_y2"])
        gt = tuple(float(row[k]) for k in ["gt_x1", "gt_y1", "gt_x2", "gt_y2"])

        pred_w = pred[2] - pred[0]
        pred_h = pred[3] - pred[1]
        gt_w = gt[2] - gt[0]
        gt_h = gt[3] - gt[1]

        candidates.append({
            "image": row["image"],
            "confidence": float(row["confidence"]),
            "iou": iou,
            "pred": pred,
            "gt": gt,
            "wr": pred_w / gt_w if gt_w else 0,
            "hr": pred_h / gt_h if gt_h else 0,
        })

# Representative cases from three IoU bands.
bands = [
    (0.40, 0.50, 4),
    (0.25, 0.40, 4),
    (0.10, 0.25, 4),
]

selected = []

for low, high, count in bands:
    band = [
        x for x in candidates
        if low <= x["iou"] < high
    ]

    # Prefer higher confidence within each band.
    band.sort(key=lambda x: x["confidence"], reverse=True)

    selected.extend(band[:count])

# If a band has fewer cases, fill from remaining highest-IoU nonzero FPs.
if len(selected) < 12:
    remaining = [
        x for x in candidates
        if x not in selected
    ]
    remaining.sort(
        key=lambda x: (x["iou"], x["confidence"]),
        reverse=True
    )
    selected.extend(remaining[:12 - len(selected)])

selected = selected[:12]

tile_w = 620
tile_h = 560
cols = 3
rows = 4

sheet = Image.new(
    "RGB",
    (tile_w * cols, tile_h * rows),
    "white"
)

draw = ImageDraw.Draw(sheet)

try:
    font = ImageFont.truetype("arial.ttf", 18)
    small_font = ImageFont.truetype("arial.ttf", 15)
except:
    font = ImageFont.load_default()
    small_font = font

for index, item in enumerate(selected):

    image_path = os.path.join(IMAGE_DIR, item["image"])

    if not os.path.exists(image_path):
        print("Missing:", image_path)
        continue

    image = Image.open(image_path).convert("RGB")

    pred = item["pred"]
    gt = item["gt"]

    # Union of GT and prediction.
    x1 = min(pred[0], gt[0])
    y1 = min(pred[1], gt[1])
    x2 = max(pred[2], gt[2])
    y2 = max(pred[3], gt[3])

    union_w = x2 - x1
    union_h = y2 - y1

    # Large contextual margin around the target.
    margin_x = max(union_w * 1.25, 80)
    margin_y = max(union_h * 1.25, 80)

    crop_x1 = max(0, int(x1 - margin_x))
    crop_y1 = max(0, int(y1 - margin_y))
    crop_x2 = min(image.width, int(x2 + margin_x))
    crop_y2 = min(image.height, int(y2 + margin_y))

    crop = image.crop(
        (crop_x1, crop_y1, crop_x2, crop_y2)
    )

    # Scale crop while preserving aspect ratio.
    available_w = tile_w - 20
    available_h = tile_h - 85

    scale = min(
        available_w / crop.width,
        available_h / crop.height
    )

    new_w = max(1, int(crop.width * scale))
    new_h = max(1, int(crop.height * scale))

    crop = crop.resize((new_w, new_h))

    # Translate boxes into crop coordinates, then scale.
    def transform_box(box):
        return (
            (box[0] - crop_x1) * scale,
            (box[1] - crop_y1) * scale,
            (box[2] - crop_x1) * scale,
            (box[3] - crop_y1) * scale,
        )

    pred_box = transform_box(pred)
    gt_box = transform_box(gt)

    tile_x = (index % cols) * tile_w
    tile_y = (index // cols) * tile_h

    image_x = tile_x + (tile_w - new_w) // 2
    image_y = tile_y + 70

    sheet.paste(crop, (image_x, image_y))

    # Move boxes into sheet coordinates.
    gt_draw = (
        gt_box[0] + image_x,
        gt_box[1] + image_y,
        gt_box[2] + image_x,
        gt_box[3] + image_y,
    )

    pred_draw = (
        pred_box[0] + image_x,
        pred_box[1] + image_y,
        pred_box[2] + image_x,
        pred_box[3] + image_y,
    )

    # BLUE = GT
    draw.rectangle(
        gt_draw,
        outline="blue",
        width=5
    )

    # RED = prediction
    draw.rectangle(
        pred_draw,
        outline="red",
        width=5
    )

    # Header.
    header = (
        f"#{index + 1}  "
        f"IoU={item['iou']:.3f}  "
        f"conf={item['confidence']:.3f}"
    )

    metrics = (
        f"Pred/GT W={item['wr']:.2f}x   "
        f"H={item['hr']:.2f}x"
    )

    draw.rectangle(
        (
            tile_x + 5,
            tile_y + 5,
            tile_x + tile_w - 5,
            tile_y + 62
        ),
        fill="white"
    )

    draw.text(
        (tile_x + 12, tile_y + 10),
        header,
        fill="black",
        font=font
    )

    draw.text(
        (tile_x + 12, tile_y + 37),
        metrics,
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
print("BLUE = ground truth")
print("RED  = model prediction")
print()
for i, item in enumerate(selected, 1):
    print(
        f"{i:02d} | IoU={item['iou']:.3f} | "
        f"conf={item['confidence']:.3f} | "
        f"W={item['wr']:.2f}x | H={item['hr']:.2f}x | "
        f"{item['image']}"
    )
