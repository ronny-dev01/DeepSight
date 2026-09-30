import csv

FILES = {
    "v1": "runs/error_analysis/ghostvision_crabpot_v1_fp_analysis.csv",
    "v5": "runs/error_analysis/ghostvision_crabpot_v5_fp_analysis.csv",
}

TARGET_RECALLS = [0.25, 0.30, 0.35, 0.40, 0.45]

print()
print("=" * 78)
print("V1 vs V5 - RECALL-MATCHED COMPARISON")
print("=" * 78)
print()
print(f"{'Model':<7} {'TargetR':<8} {'Conf':<7} {'P':<8} {'R':<8} {'F1':<8} {'TP':<6} {'FP':<6} {'BG-FP':<8} {'Near-FP':<8}")

for model, path in FILES.items():

    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))

    thresholds = sorted({
        round(float(r["confidence"]), 3)
        for r in rows
        if float(r["confidence"]) >= 0.01
    })

    for target in TARGET_RECALLS:

        best = None

        for threshold in thresholds:

            selected = [
                r for r in rows
                if float(r["confidence"]) >= threshold
            ]

            tp = sum(r["type"] == "TP" for r in selected)
            fp = sum(r["type"] == "FP" for r in selected)

            recall = tp / 567
            precision = tp / (tp + fp) if tp + fp else 0
            f1 = (
                2 * precision * recall / (precision + recall)
                if precision + recall
                else 0
            )

            background_fp = sum(
                r["type"] == "FP" and float(r["best_iou"]) == 0
                for r in selected
            )

            near_miss_fp = sum(
                r["type"] == "FP"
                and 0 < float(r["best_iou"]) < 0.50
                for r in selected
            )

            distance = abs(recall - target)

            candidate = (
                distance,
                threshold,
                precision,
                recall,
                f1,
                tp,
                fp,
                background_fp,
                near_miss_fp,
            )

            if best is None or candidate[0] < best[0]:
                best = candidate

        _, threshold, precision, recall, f1, tp, fp, bg, near = best

        print(
            f"{model:<7} "
            f"{target:<8.2f} "
            f"{threshold:<7.3f} "
            f"{precision:<8.3f} "
            f"{recall:<8.3f} "
            f"{f1:<8.3f} "
            f"{tp:<6} "
            f"{fp:<6} "
            f"{bg:<8} "
            f"{near:<8}"
        )

    print()

