import csv
from collections import defaultdict, Counter

PATH = "runs/error_analysis/ghostvision_crabpot_v1_fp_analysis.csv"

groups = defaultdict(Counter)

with open(PATH, newline="") as f:
    for row in csv.DictReader(f):
        image = row["image"]
        kind = row["type"]

        # Source prefix: everything before the first underscore
        source = image.split("_")[0]

        groups[source][kind] += 1

print("Source-level error distribution")
print()
print(f"{'SOURCE':<15} {'TP':>6} {'FP':>6} {'TOTAL':>7} {'FP_RATE':>8}")

for source, counts in sorted(
    groups.items(),
    key=lambda x: sum(x[1].values()),
    reverse=True
):
    tp = counts["TP"]
    fp = counts["FP"]
    total = tp + fp
    fp_rate = fp / total if total else 0

    print(
        f"{source:<15} "
        f"{tp:>6} "
        f"{fp:>6} "
        f"{total:>7} "
        f"{fp_rate:>7.1%}"
    )
