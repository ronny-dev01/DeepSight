import csv
from collections import Counter

PATH = "runs/error_analysis/ghostvision_crabpot_v5_fp_analysis.csv"

groups = {
    "background_fp": [],
    "near_miss_fp": [],
}

with open(PATH, newline="") as f:
    for row in csv.DictReader(f):
        if row["type"] != "FP":
            continue

        iou = float(row["best_iou"])
        conf = float(row["confidence"])

        if iou == 0:
            groups["background_fp"].append((conf, row["image"]))
        elif 0 < iou < 0.50:
            groups["near_miss_fp"].append((conf, row["image"]))

for name, items in groups.items():
    print()
    print("=" * 60)
    print(name.upper())
    print("=" * 60)

    confidences = [x[0] for x in items]

    print(f"Count: {len(items)}")
    print(f"Mean confidence: {sum(confidences) / len(confidences):.4f}")
    print(f"Max confidence: {max(confidences):.4f}")
    print()

    buckets = Counter()

    for conf in confidences:
        if conf < 0.05:
            buckets["0.01-0.049"] += 1
        elif conf < 0.10:
            buckets["0.05-0.099"] += 1
        elif conf < 0.20:
            buckets["0.10-0.199"] += 1
        elif conf < 0.30:
            buckets["0.20-0.299"] += 1
        elif conf < 0.40:
            buckets["0.30-0.399"] += 1
        elif conf < 0.50:
            buckets["0.40-0.499"] += 1
        else:
            buckets["0.50+"] += 1

    for bucket in [
        "0.01-0.049",
        "0.05-0.099",
        "0.10-0.199",
        "0.20-0.299",
        "0.30-0.399",
        "0.40-0.499",
        "0.50+",
    ]:
        print(f"{bucket:<12} {buckets[bucket]:>5}")

    print()
    print("Top 10:")
    for conf, image in sorted(items, reverse=True)[:10]:
        print(f"  conf={conf:.4f}  {image}")
