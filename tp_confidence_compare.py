import csv
import os
from collections import defaultdict

LABEL_DIR = "data/derived/ghostvision_yolo/test/labels"

FILES = {
    "v1": "runs/error_analysis/ghostvision_crabpot_v1_raw_predictions.csv",
    "v4": "runs/error_analysis/ghostvision_crabpot_v4_raw_predictions.csv",
}

BINS = [0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 1.01]
NAMES = [".01-.05", ".05-.10", ".10-.15", ".15-.20", ".20-.25", ".25-.30", ".30-.40", ".40-.50", ".50+"]

def iou(a, b):
    iw = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    ih = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = iw * ih
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter + 1e-12)

print("TP confidence distribution (IoU >= 0.50)")
print()

for model, path in FILES.items():
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

    counts = [0] * 9
    total = 0

    for image, boxes in preds.items():
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

        matched = set()

        for prediction in sorted(boxes, reverse=True):
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
                total += 1

                confidence = prediction[0]

                for i in range(9):
                    if BINS[i] <= confidence < BINS[i + 1]:
                        counts[i] += 1
                        break

    print(model, " | ", " | ".join(
        f"{name}: {count}"
        for name, count in zip(NAMES, counts)
    ))
    print("Total TP:", total)
    print()
