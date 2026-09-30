import csv

FILES = {
    "v1": "runs/error_analysis/ghostvision_crabpot_v1_fp_analysis.csv",
    "v5": "runs/error_analysis/ghostvision_crabpot_v5_fp_analysis.csv",
}

THRESHOLDS = [0.20, 0.25, 0.30, 0.35, 0.40]

print(f"{'model':<6} {'conf':<6} {'totalFP':<8} {'backgroundFP':<14} {'nearMissFP':<12} {'bg%':<6}")

for model, path in FILES.items():
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))

    for threshold in THRESHOLDS:
        fps = [
            r for r in rows
            if r["type"] == "FP"
            and float(r["confidence"]) >= threshold
        ]

        background = [
            r for r in fps
            if float(r["best_iou"]) == 0
        ]

        near_miss = [
            r for r in fps
            if 0 < float(r["best_iou"]) < 0.50
        ]

        bg_pct = 100 * len(background) / len(fps) if fps else 0

        print(
            f"{model:<6} "
            f"{threshold:<6.2f} "
            f"{len(fps):<8} "
            f"{len(background):<14} "
            f"{len(near_miss):<12} "
            f"{bg_pct:<6.1f}"
        )
