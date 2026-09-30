import csv
import math

PATH = "runs/error_analysis/ghostvision_crabpot_v1_fp_analysis.csv"

rows = []

with open(PATH, newline="") as f:
    for row in csv.DictReader(f):
        if row["type"] != "FP":
            continue

        iou = float(row["best_iou"])

        if 0.40 <= iou < 0.50:
            px1 = float(row["pred_x1"])
            py1 = float(row["pred_y1"])
            px2 = float(row["pred_x2"])
            py2 = float(row["pred_y2"])

            gx1 = float(row["gt_x1"])
            gy1 = float(row["gt_y1"])
            gx2 = float(row["gt_x2"])
            gy2 = float(row["gt_y2"])

            pw = px2 - px1
            ph = py2 - py1
            gw = gx2 - gx1
            gh = gy2 - gy1

            pcx = (px1 + px2) / 2
            pcy = (py1 + py2) / 2
            gcx = (gx1 + gx2) / 2
            gcy = (gy1 + gy2) / 2

            center_distance = math.sqrt(
                (pcx - gcx) ** 2 +
                (pcy - gcy) ** 2
            )

            width_ratio = pw / gw if gw else 0
            height_ratio = ph / gh if gh else 0
            area_ratio = (pw * ph) / (gw * gh) if gw * gh else 0

            rows.append({
                "image": row["image"],
                "confidence": float(row["confidence"]),
                "iou": iou,
                "center_distance": center_distance,
                "width_ratio": width_ratio,
                "height_ratio": height_ratio,
                "area_ratio": area_ratio,
            })

print("Near-miss geometry analysis: IoU 0.40-0.49")
print()
print(f"Count: {len(rows)}")

print()
print("Average geometry")
print(f"Mean center distance: {sum(r['center_distance'] for r in rows) / len(rows):.2f} px")
print(f"Mean width ratio:     {sum(r['width_ratio'] for r in rows) / len(rows):.2f}x")
print(f"Mean height ratio:    {sum(r['height_ratio'] for r in rows) / len(rows):.2f}x")
print(f"Mean area ratio:      {sum(r['area_ratio'] for r in rows) / len(rows):.2f}x")

print()
print("Box-size categories")

categories = {
    "much smaller (<0.67x area)": 0,
    "similar (0.67x-1.50x area)": 0,
    "much larger (>1.50x area)": 0,
}

for r in rows:
    if r["area_ratio"] < 0.67:
        categories["much smaller (<0.67x area)"] += 1
    elif r["area_ratio"] <= 1.50:
        categories["similar (0.67x-1.50x area)"] += 1
    else:
        categories["much larger (>1.50x area)"] += 1

for name, count in categories.items():
    print(f"{name:<35} {count:>4} ({count / len(rows):.1%})")

print()
print("Top 15 by IoU")

for r in sorted(rows, key=lambda x: x["iou"], reverse=True)[:15]:
    print(
        f"IoU={r['iou']:.4f} "
        f"conf={r['confidence']:.4f} "
        f"center={r['center_distance']:.1f}px "
        f"width={r['width_ratio']:.2f}x "
        f"height={r['height_ratio']:.2f}x "
        f"area={r['area_ratio']:.2f}x "
        f"{r['image']}"
    )
