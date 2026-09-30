import csv

PATH = "runs/error_analysis/ghostvision_crabpot_v1_fp_analysis.csv"

rows = []

with open(PATH, newline="") as f:
    for row in csv.DictReader(f):
        if row["type"] == "FP":
            rows.append(row)

rows.sort(key=lambda r: float(r["confidence"]), reverse=True)

print("Top 20 highest-confidence false positives")
print()

for i, row in enumerate(rows[:20], 1):
    print(
        f"{i:>2}. "
        f"conf={float(row['confidence']):.4f} "
        f"best_iou={float(row['best_iou']):.4f} "
        f"{row['image']}"
    )
