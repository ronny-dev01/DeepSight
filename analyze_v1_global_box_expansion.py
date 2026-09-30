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
    iw = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    ih = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = iw * ih

    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    union = area_a + area_b - inter

    return inter / (union + 1e-12)


def expand_box(box, factor):
    x1, y1, x2, y2 = box

    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0

    half_w = (x2 - x1) * factor / 2.0
    half_h = (y2 - y1) * factor / 2.0

    return (
        max(0.0, cx - half_w),
        max(0.0, cy - half_h),
        min(640.0, cx + half_w),
        min(640.0, cy + half_h),
    )


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

factors = [1.00, 1.10, 1.20, 1.30, 1.40, 1.50, 1.60, 1.75, 2.00]
conf_thresholds = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]

for factor in factors:

    print()
    print("=" * 78)
    print(f"EXPANSION FACTOR: {factor:.2f}x")
    print("=" * 78)
    print("conf   TP    FP    FN    precision  recall")

    for conf in conf_thresholds:

        tp = 0
        fp = 0

        for image, boxes in preds.items():

            selected = sorted(
                [x for x in boxes if x[0] >= conf],
                key=lambda x: x[0],
                reverse=True,
            )

            matched = set()

            for prediction in selected:

                pred_box = expand_box(prediction[1:], factor)

                best_iou = 0.0
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
            f"{precision:9.3f} "
            f"{recall:6.3f}"
        )
