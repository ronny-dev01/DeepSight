import csv
import os
from collections import defaultdict

PRED = "runs/error_analysis/ghostvision_crabpot_v5_raw_predictions.csv"
LABEL_DIR = "data/derived/ghostvision_yolo/test/labels"
OUT = "runs/error_analysis/ghostvision_crabpot_v5_fp_analysis.csv"

preds = defaultdict(list)

with open(PRED, newline="") as f:
    for row in csv.DictReader(f):
        preds[row["image"]].append({
            "confidence": float(row["confidence"]),
            "bbox": (
                float(row["pred_x1"]),
                float(row["pred_y1"]),
                float(row["pred_x2"]),
                float(row["pred_y2"]),
            ),
        })

def iou(a, b):
    iw = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    ih = max(0, min(a[3], b[3]) - max(a[1], b[1]))

    inter = iw * ih

    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])

    union = area_a + area_b - inter

    return inter / (union + 1e-12)

gts = {}

for image in preds:

    path = os.path.join(
        LABEL_DIR,
        os.path.splitext(image)[0] + ".txt"
    )

    boxes = []

    with open(path) as f:
        for line in f:
            _, cx, cy, w, h = map(float, line.split())

            boxes.append((
                (cx - w / 2) * 640,
                (cy - h / 2) * 640,
                (cx + w / 2) * 640,
                (cy + h / 2) * 640,
            ))

    gts[image] = boxes

rows = []

for image, predictions in preds.items():

    predictions = sorted(
        [p for p in predictions if p["confidence"] >= 0.01],
        key=lambda x: x["confidence"],
        reverse=True,
    )

    matched = set()

    for prediction in predictions:

        best_iou = 0
        best_index = -1

        for index, gt in enumerate(gts.get(image, [])):

            if index in matched:
                continue

            current = iou(prediction["bbox"], gt)

            if current > best_iou:
                best_iou = current
                best_index = index

        if best_iou >= 0.50:

            matched.add(best_index)

            gt = gts[image][best_index]

            rows.append([
                image,
                "TP",
                prediction["confidence"],
                best_iou,
                *prediction["bbox"],
                *gt,
            ])

        else:

            if best_index >= 0:
                gt = gts[image][best_index]
                gt_values = gt
            else:
                gt_values = ("", "", "", "")

            rows.append([
                image,
                "FP",
                prediction["confidence"],
                best_iou,
                *prediction["bbox"],
                *gt_values,
            ])

rows.sort(
    key=lambda x: (
        x[1] != "FP",
        -float(x[2]),
    )
)

with open(OUT, "w", newline="") as f:

    writer = csv.writer(f)

    writer.writerow([
        "image",
        "type",
        "confidence",
        "best_iou",
        "pred_x1",
        "pred_y1",
        "pred_x2",
        "pred_y2",
        "gt_x1",
        "gt_y1",
        "gt_x2",
        "gt_y2",
    ])

    writer.writerows(rows)

fps = sum(r[1] == "FP" for r in rows)
tps = sum(r[1] == "TP" for r in rows)

print("Saved:", OUT)
print("TP:", tps)
print("FP:", fps)
print("Total analyzed:", len(rows))
print()
print("Top 20 highest-confidence false positives:")

count = 0

for row in rows:

    if row[1] == "FP":

        print(
            f"{row[0]} | "
            f"conf={float(row[2]):.4f} | "
            f"best_iou={float(row[3]):.4f}"
        )

        count += 1

        if count >= 20:
            break
