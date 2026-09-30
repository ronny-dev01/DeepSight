import csv
import os
from collections import defaultdict

LABEL_DIR = "data/derived/ghostvision_yolo/test/labels"

FILES = {
    "v1": "runs/error_analysis/ghostvision_crabpot_v1_raw_predictions.csv",
    "v4": "runs/error_analysis/ghostvision_crabpot_v4_raw_predictions.csv",
}

THRESHOLDS = [round(x / 100, 2) for x in range(1, 51)]

def iou(a, b):
    iw = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    ih = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = iw * ih

    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])

    return inter / (area_a + area_b - inter + 1e-12)

def load_predictions(path):
    preds = defaultdict(list)

    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            preds[row["image"]].append((
                float(row["confidence"]),
                float(row["x1"]),
                float(row["y1"]),
                float(row["x2"]),
                float(row["y2"]),
            ))

    return preds

def load_gts(image):
    label_path = os.path.join(
        LABEL_DIR,
        os.path.splitext(image)[0] + ".txt"
    )

    gts = []

    with open(label_path) as f:
        for line in f:
            _, cx, cy, w, h = map(float, line.split())

            gts.append((
                (cx - w / 2) * 640,
                (cy - h / 2) * 640,
                (cx + w / 2) * 640,
                (cy + h / 2) * 640,
            ))

    return gts

def evaluate(preds, threshold):
    tp = 0
    fp = 0
    total_gt = 0

    for image, boxes in preds.items():
        gts = load_gts(image)
        total_gt += len(gts)

        selected = [
            p for p in boxes
            if p[0] >= threshold
        ]

        selected.sort(reverse=True)

        matched = set()

        for prediction in selected:
            best_iou = 0
            best_index = -1

            for index, gt in enumerate(gts):
                if index in matched:
                    continue

                current_iou = iou(prediction[1:], gt)

                if current_iou > best_iou:
                    best_iou = current_iou
                    best_index = index

            if best_iou >= 0.50:
                matched.add(best_index)
                tp += 1
            else:
                fp += 1

    fn = total_gt - tp

    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0
    )

    return tp, fp, fn, precision, recall, f1

for model, path in FILES.items():
    preds = load_predictions(path)

    print()
    print("=" * 78)
    print(model.upper())
    print("=" * 78)
    print("threshold |   TP |   FP |   FN | precision | recall |    F1")
    print("-" * 78)

    best_f1 = (-1, None)

    for threshold in THRESHOLDS:
        tp, fp, fn, precision, recall, f1 = evaluate(
            preds,
            threshold
        )

        if f1 > best_f1[0]:
            best_f1 = (f1, threshold)

        print(
            f"{threshold:9.2f} | "
            f"{tp:4d} | "
            f"{fp:4d} | "
            f"{fn:4d} | "
            f"{precision:9.3f} | "
            f"{recall:6.3f} | "
            f"{f1:6.3f}"
        )

    print()
    print(
        f"Best F1 in this diagnostic: "
        f"{best_f1[0]:.3f} at threshold {best_f1[1]:.2f}"
    )
