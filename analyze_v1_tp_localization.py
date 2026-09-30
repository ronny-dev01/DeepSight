import csv
import os
import statistics

PRED_PATH = "runs/error_analysis/ghostvision_crabpot_v1_raw_predictions.csv"
LABEL_DIR = "data/derived/ghostvision_yolo/test/labels"

IOU_THRESHOLD = 0.50

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

            cls, cx, cy, w, h = map(float, parts)

            # Test images are 640x640.
            x1 = (cx - w / 2) * 640
            y1 = (cy - h / 2) * 640
            x2 = (cx + w / 2) * 640
            y2 = (cy + h / 2) * 640

            gts.append((x1, y1, x2, y2))

    return gts


predictions = {}

with open(PRED_PATH, newline="") as f:
    for row in csv.DictReader(f):

        image = row["image"]

        bbox = (
            float(row["x1"]),
            float(row["y1"]),
            float(row["x2"]),
            float(row["y2"]),
        )

        predictions.setdefault(image, []).append({
            "confidence": float(row["confidence"]),
            "bbox": bbox,
        })


results = []

for image, preds in predictions.items():

    gts = load_gt(image)

    if not gts:
        continue

    # Highest-confidence predictions first.
    preds = sorted(
        preds,
        key=lambda p: p["confidence"],
        reverse=True
    )

    used_gt = set()

    for pred in preds:

        best_iou = 0.0
        best_index = -1

        for i, gt in enumerate(gts):

            if i in used_gt:
                continue

            score = iou(pred["bbox"], gt)

            if score > best_iou:
                best_iou = score
                best_index = i

        if best_iou < IOU_THRESHOLD:
            continue

        gt = gts[best_index]
        used_gt.add(best_index)

        px1, py1, px2, py2 = pred["bbox"]
        gx1, gy1, gx2, gy2 = gt

        pred_w = px2 - px1
        pred_h = py2 - py1

        gt_w = gx2 - gx1
        gt_h = gy2 - gy1

        pred_cx = (px1 + px2) / 2
        pred_cy = (py1 + py2) / 2

        gt_cx = (gx1 + gx2) / 2
        gt_cy = (gy1 + gy2) / 2

        center_dx = pred_cx - gt_cx
        center_dy = pred_cy - gt_cy

        center_distance = (
            (center_dx ** 2 + center_dy ** 2) ** 0.5
        )

        results.append({
            "image": image,
            "confidence": pred["confidence"],
            "iou": best_iou,

            "pred_w": pred_w,
            "pred_h": pred_h,

            "gt_w": gt_w,
            "gt_h": gt_h,

            "width_ratio": pred_w / gt_w if gt_w else 0,
            "height_ratio": pred_h / gt_h if gt_h else 0,

            "center_dx": center_dx,
            "center_dy": center_dy,
            "center_distance": center_distance,

            "center_distance_norm": (
                center_distance /
                ((gt_w ** 2 + gt_h ** 2) ** 0.5)
                if gt_w > 0 and gt_h > 0
                else 0
            ),
        })


def stats(values):
    if not values:
        return "n=0"

    return (
        f"n={len(values)}, "
        f"median={statistics.median(values):.4f}, "
        f"mean={statistics.mean(values):.4f}"
    )


print()
print("GHOSTVISION V1 — TRUE POSITIVE LOCALIZATION AUDIT")
print("=" * 60)
print()
print(f"Matched TP detections: {len(results)}")
print()

# Overall.
print("OVERALL")
print("-" * 60)

for key in [
    "iou",
    "width_ratio",
    "height_ratio",
    "center_distance",
    "center_distance_norm",
]:
    print(f"{key:24s}: {stats([r[key] for r in results])}")

print()

# Confidence groups.
bands = [
    ("0.01-0.10", 0.01, 0.10),
    ("0.10-0.20", 0.10, 0.20),
    ("0.20-0.30", 0.20, 0.30),
    ("0.30-0.40", 0.30, 0.40),
    ("0.40-0.50", 0.40, 0.50),
    ("0.50+", 0.50, 999),
]

for name, low, high in bands:

    group = [
        r for r in results
        if low <= r["confidence"] < high
    ]

    if not group:
        continue

    print(name)
    print("-" * 60)

    print(
        f"count={len(group)} | "
        f"IoU median={statistics.median(r['iou'] for r in group):.3f} | "
        f"W ratio median={statistics.median(r['width_ratio'] for r in group):.3f} | "
        f"H ratio median={statistics.median(r['height_ratio'] for r in group):.3f} | "
        f"center norm median={statistics.median(r['center_distance_norm'] for r in group):.3f}"
    )

print()

# Width/height ratio categories.
print("BOX SIZE RATIO")
print("-" * 60)

for label, condition in [
    ("<0.50x", lambda r: r["width_ratio"] < 0.50),
    ("0.50-0.75x", lambda r: 0.50 <= r["width_ratio"] < 0.75),
    ("0.75-1.00x", lambda r: 0.75 <= r["width_ratio"] < 1.00),
    ("1.00-1.25x", lambda r: 1.00 <= r["width_ratio"] < 1.25),
    ("1.25-1.50x", lambda r: 1.25 <= r["width_ratio"] < 1.50),
    (">=1.50x", lambda r: r["width_ratio"] >= 1.50),
]:
    count = sum(condition(r) for r in results)

    print(
        f"{label:12s}: {count:4d} "
        f"({count / len(results) * 100:.1f}%)"
    )

print()

print("Done.")
