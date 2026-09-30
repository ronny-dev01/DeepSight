from pathlib import Path
import csv
import statistics

CSV_PATH = Path("runs/error_analysis/ghostvision_crabpot_v1_fp_analysis.csv")

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


def expand_box(box, factor):
    x1, y1, x2, y2 = box

    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0

    half_w = (x2 - x1) * factor / 2.0
    half_h = (y2 - y1) * factor / 2.0

    return (
        cx - half_w,
        cy - half_h,
        cx + half_w,
        cy + half_h,
    )


rows = []

with CSV_PATH.open(newline="") as f:
    for row in csv.DictReader(f):
        if row["type"] != "FP":
            continue

        if not row["gt_x1"]:
            continue

        pred = (
            float(row["pred_x1"]),
            float(row["pred_y1"]),
            float(row["pred_x2"]),
            float(row["pred_y2"]),
        )

        gt = (
            float(row["gt_x1"]),
            float(row["gt_y1"]),
            float(row["gt_x2"]),
            float(row["gt_y2"]),
        )

        rows.append((pred, gt))


print(f"Non-zero-IoU FP cases analyzed: {len(rows)}")
print()

factors = [1.00, 1.10, 1.20, 1.30, 1.40, 1.50, 1.60, 1.75, 2.00]

for factor in factors:
    values = [
        iou(expand_box(pred, factor), gt)
        for pred, gt in rows
    ]

    recovered = sum(v >= 0.50 for v in values)
    recovered_030 = sum(v >= 0.30 for v in values)

    print(
        f"{factor:>4.2f}x  "
        f"mean_IoU={statistics.mean(values):.3f}  "
        f"median_IoU={statistics.median(values):.3f}  "
        f"IoU>=0.30={recovered_030:>3}/{len(values)}  "
        f"IoU>=0.50={recovered:>3}/{len(values)}"
    )

print()
print("Original:")
original = [
    iou(pred, gt)
    for pred, gt in rows
]

print(
    f"1.00x  mean_IoU={statistics.mean(original):.3f}  "
    f"median_IoU={statistics.median(original):.3f}"
)
