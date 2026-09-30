import csv
import os
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont

PRED_PATH = "runs/error_analysis/ghostvision_crabpot_v1_raw_predictions.csv"
LABEL_DIR = "data/derived/ghostvision_yolo/test/labels"
IMAGE_ROOT = "data/derived/ghostvision_yolo/test/images"
OUT_PATH = "runs/error_analysis/v1_high_conf_fp_vs_tp.jpg"

IOU_THRESHOLD = 0.50
MIN_CONF = 0.20

def iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)

    inter = iw * ih

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)

    union = area_a + area_b - inter

    return inter / union if union > 0 else 0.0


def load_gt(image_name):
    label_name = os.path.splitext(image_name)[0] + ".txt"
    path = os.path.join(LABEL_DIR, label_name)

    gts = []

    if not os.path.exists(path):
        return gts

    with open(path) as f:
        for line in f:
            parts = line.split()

            if len(parts) != 5:
                continue

            _, cx, cy, w, h = map(float, parts)

            gts.append((
                (cx - w / 2) * 640,
                (cy - h / 2) * 640,
                (cx + w / 2) * 640,
                (cy + h / 2) * 640,
            ))

    return gts


predictions = defaultdict(list)

with open(PRED_PATH, newline="") as f:
    for row in csv.DictReader(f):
        predictions[row["image"]].append({
            "confidence": float(row["confidence"]),
            "bbox": (
                float(row["x1"]),
                float(row["y1"]),
                float(row["x2"]),
                float(row["y2"]),
            ),
        })


tp_rows = []
fp_rows = []

for image, preds in predictions.items():

    gts = load_gt(image)

    preds = sorted(
        preds,
        key=lambda p: p["confidence"],
        reverse=True
    )

    used_gt = set()

    for pred in preds:

        if pred["confidence"] < MIN_CONF:
            continue

        best_iou = 0.0
        best_idx = -1

        for i, gt in enumerate(gts):

            if i in used_gt:
                continue

            score = iou(pred["bbox"], gt)

            if score > best_iou:
                best_iou = score
                best_idx = i

        if best_iou >= IOU_THRESHOLD:
            used_gt.add(best_idx)

            tp_rows.append({
                "image": image,
                "confidence": pred["confidence"],
                "iou": best_iou,
                "bbox": pred["bbox"],
                "gt": gts[best_idx],
            })

        else:
            fp_rows.append({
                "image": image,
                "confidence": pred["confidence"],
                "iou": best_iou,
                "bbox": pred["bbox"],
                "gt": gts[best_idx] if best_idx >= 0 else None,
            })


# ------------------------------------------------------------
# Confidence-bin sampling.
# Keep TP and FP distributions comparable.
# ------------------------------------------------------------

bins = [
    ("0.20-0.30", 0.20, 0.30),
    ("0.30-0.40", 0.30, 0.40),
    ("0.40+", 0.40, 999),
]

selected_tp = []
selected_fp = []

for name, low, high in bins:

    tps = sorted(
        [
            r for r in tp_rows
            if low <= r["confidence"] < high
        ],
        key=lambda r: r["confidence"],
        reverse=True
    )

    fps = sorted(
        [
            r for r in fp_rows
            if low <= r["confidence"] < high
        ],
        key=lambda r: r["confidence"],
        reverse=True
    )

    # Maximum 10 of each per confidence band.
    selected_tp.extend(tps[:10])
    selected_fp.extend(fps[:10])


print()
print("GHOSTVISION V1 — HIGH-CONFIDENCE FP vs TP AUDIT")
print("=" * 65)
print()
print(f"All TP detections >= {MIN_CONF:.2f}: {len(tp_rows)}")
print(f"All FP detections >= {MIN_CONF:.2f}: {len(fp_rows)}")
print()

for name, low, high in bins:

    tp_count = sum(
        low <= r["confidence"] < high
        for r in tp_rows
    )

    fp_count = sum(
        low <= r["confidence"] < high
        for r in fp_rows
    )

    print(
        f"{name:12s} | "
        f"TP={tp_count:4d} | "
        f"FP={fp_count:4d}"
    )

print()
print("Selected for visual audit:")
print(f"TP: {len(selected_tp)}")
print(f"FP: {len(selected_fp)}")
print()


def resize_with_boxes(row, kind):

    path = os.path.join(IMAGE_ROOT, row["image"])

    img = Image.open(path).convert("RGB")
    img = img.resize((320, 320))

    draw = ImageDraw.Draw(img)

    scale = 320 / 640

    x1, y1, x2, y2 = row["bbox"]

    pred_box = (
        x1 * scale,
        y1 * scale,
        x2 * scale,
        y2 * scale,
    )

    if kind == "TP":
        # Prediction = red
        draw.rectangle(pred_box, outline="red", width=3)

        if row["gt"] is not None:
            gx1, gy1, gx2, gy2 = row["gt"]

            gt_box = (
                gx1 * scale,
                gy1 * scale,
                gx2 * scale,
                gy2 * scale,
            )

            # GT = blue
            draw.rectangle(gt_box, outline="blue", width=2)

    else:
        # FP prediction = red
        draw.rectangle(pred_box, outline="red", width=3)

        # If it overlaps a GT, show that GT in blue.
        if row["gt"] is not None and row["iou"] > 0:
            gx1, gy1, gx2, gy2 = row["gt"]

            gt_box = (
                gx1 * scale,
                gy1 * scale,
                gx2 * scale,
                gy2 * scale,
            )

            draw.rectangle(gt_box, outline="blue", width=2)

    return img


# ------------------------------------------------------------
# Build rows:
# FP on left, TP on right.
# ------------------------------------------------------------

pairs = []

for i in range(max(len(selected_fp), len(selected_tp))):
    fp = selected_fp[i] if i < len(selected_fp) else None
    tp = selected_tp[i] if i < len(selected_tp) else None
    pairs.append((fp, tp))


cell_w = 320
cell_h = 365

sheet_w = cell_w * 2
sheet_h = cell_h * len(pairs)

sheet = Image.new("RGB", (sheet_w, sheet_h), "white")

draw = ImageDraw.Draw(sheet)

for row_idx, (fp, tp) in enumerate(pairs):

    y = row_idx * cell_h

    if fp is not None:

        img = resize_with_boxes(fp, "FP")
        sheet.paste(img, (0, y + 45))

        draw.text(
            (5, y + 5),
            (
                f"FP  conf={fp['confidence']:.3f} "
                f"IoU={fp['iou']:.3f}"
            ),
            fill="red",
        )

        draw.text(
            (5, y + 25),
            fp["image"][:42],
            fill="black",
        )

    if tp is not None:

        img = resize_with_boxes(tp, "TP")
        sheet.paste(img, (cell_w, y + 45))

        draw.text(
            (cell_w + 5, y + 5),
            (
                f"TP  conf={tp['confidence']:.3f} "
                f"IoU={tp['iou']:.3f}"
            ),
            fill="blue",
        )

        draw.text(
            (cell_w + 5, y + 25),
            tp["image"][:42],
            fill="black",
        )


os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
sheet.save(OUT_PATH, quality=95)

print()
print(f"Saved visual audit:")
print(OUT_PATH)
print()
print("Legend:")
print("RED  = model prediction")
print("BLUE = ground truth")
print()
print("Done.")
