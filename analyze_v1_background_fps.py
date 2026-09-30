import csv
from collections import Counter

CSV_PATH = "runs/error_analysis/ghostvision_crabpot_v1_fp_analysis.csv"

background = []

with open(CSV_PATH, newline="") as f:
    for row in csv.DictReader(f):
        if row["type"] != "FP":
            continue

        if row["best_iou"] != "" and float(row["best_iou"]) == 0.0:
            background.append(row)

print(f"Background FPs: {len(background)}")
print()

bins = [
    ("0.01-0.05", 0.01, 0.05),
    ("0.05-0.10", 0.05, 0.10),
    ("0.10-0.20", 0.10, 0.20),
    ("0.20-0.30", 0.20, 0.30),
    ("0.30-0.40", 0.30, 0.40),
    ("0.40-0.50", 0.40, 0.50),
    ("0.50+", 0.50, float("inf")),
]

print("Confidence distribution")
print("-" * 55)

for name, low, high in bins:
    values = [
        float(row["confidence"])
        for row in background
        if low <= float(row["confidence"]) < high
    ]

    print(
        f"{name:>10}  "
        f"count={len(values):4d}  "
        f"percent={len(values) / len(background) * 100:6.2f}%  "
        f"max={max(values):.4f}" if values else
        f"{name:>10}  count=   0"
    )

print()
print("High-confidence background FPs (>= 0.30)")
print("-" * 90)

high = sorted(
    [
        row for row in background
        if float(row["confidence"]) >= 0.30
    ],
    key=lambda r: float(r["confidence"]),
    reverse=True,
)

for i, row in enumerate(high[:50], 1):
    print(
        f"{i:2d}. "
        f"conf={float(row['confidence']):.4f}  "
        f"image={row['image']}"
    )

print()
print(f"Total background FPs >= 0.30: {len(high)}")
