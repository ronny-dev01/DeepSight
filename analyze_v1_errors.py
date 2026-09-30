import csv
import os
from collections import defaultdict

PRED = "runs/error_analysis/ghostvision_crabpot_v1_raw_predictions.csv"
LABEL_DIR = "data/derived/ghostvision_yolo/test/labels"

preds = defaultdict(list)

with open(PRED, newline="") as f:
    for row in csv.DictReader(f):
        preds[row["image"]].append((
            float(row["confidence"]),
            float(row["x1"]),
            float(row["y1"]),
            float(row["x2"]),
            float(row["y2"]),
        ))

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
    label_path = os.path.join(
        LABEL_DIR,
        os.path.splitext(image)[0] + ".txt"
    )

    boxes = []

    with open(label_path) as f:
        for line in f:
            parts = list(map(float, line.split()))

            _, cx, cy, w, h = parts

            boxes.append((
                (cx - w / 2) * 640,
                (cy - h / 2) * 640,
                (cx + w / 2) * 640,
                (cy + h / 2) * 640,
            ))

    gts[image] = boxes

total_gt = sum(len(x) for x in gts.values())

print("GT:", total_gt)
print("Raw predictions:", sum(len(x) for x in preds.values()))
print()
print("IoU 0.50")
print("conf   TP    FP    FN    precision recall")

for conf in [0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]:

    tp = 0
    fp = 0

    for image, boxes in preds.items():

        selected = sorted(
            [x for x in boxes if x[0] >= conf],
            reverse=True
        )

        matched = set()

        for prediction in selected:

            pred_box = prediction[1:]

            best_iou = 0
            best_index = -1

            for index, gt_box in enumerate(gts.get(image, [])):

                if index in matched:
                    continue

                current_iou = iou(pred_box, gt_box)

                if current_iou > best_iou:
                    best_iou = current_iou
                    best_index = index

            if best_iou >= 0.50:
                tp += 1
                matched.add(best_index)
            else:
                fp += 1

    fn = total_gt - tp

    precision = tp / (tp + fp + 1e-12)
    recall = tp / (tp + fn + 1e-12)

    print(
        f"{conf:0.2f} "
        f"{tp:5d} "
        f"{fp:5d} "
        f"{fn:5d} "
        f"{precision:0.3f} "
        f"{recall:0.3f}"
    )
