import csv
from collections import Counter

PATH = "runs/error_analysis/ghostvision_crabpot_v1_fp_analysis.csv"

bins = Counter()
conf_by_bin = {}

with open(PATH, newline="") as f:
    for row in csv.DictReader(f):
        if row["type"] != "FP":
            continue

        iou = float(row["best_iou"])
        conf = float(row["confidence"])

        if iou == 0:
            bucket = "0.00"
        elif iou < 0.10:
            bucket = "0.01-0.09"
        elif iou < 0.25:
            bucket = "0.10-0.24"
        elif iou < 0.40:
            bucket = "0.25-0.39"
        else:
            bucket = "0.40-0.49"

        bins[bucket] += 1
        conf_by_bin.setdefault(bucket, []).append(conf)

order = [
    "0.00",
    "0.01-0.09",
    "0.10-0.24",
    "0.25-0.39",
    "0.40-0.49",
]

print("V1 FP IoU distribution")
print()
print(f"{'IOU RANGE':<15} {'COUNT':>8} {'MEAN CONF':>12} {'MAX CONF':>10}")
print("-" * 50)

for bucket in order:
    values = conf_by_bin.get(bucket, [])

    if values:
        mean_conf = sum(values) / len(values)
        max_conf = max(values)
    else:
        mean_conf = 0
        max_conf = 0

    print(
        f"{bucket:<15} "
        f"{bins[bucket]:>8} "
        f"{mean_conf:>12.4f} "
        f"{max_conf:>10.4f}"
    )
