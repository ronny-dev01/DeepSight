from pathlib import Path
import csv
from ultralytics import YOLO

MODEL = "runs/detect/runs/train/ghostvision_crabpot_v1/weights/best.pt"
IMAGE_ROOT = Path("data/derived/ghostvision_yolo/train/images")
LABEL_ROOT = Path("data/derived/ghostvision_yolo/train/labels")
OUT_CSV = Path("runs/error_analysis/v1_train_background_fps.csv")

model = YOLO(MODEL)

rows = []

images = sorted(IMAGE_ROOT.glob("*"))

print(f"Training images: {len(images)}")

results = model.predict(
    source=str(IMAGE_ROOT),
    conf=0.30,
    iou=0.45,
    imgsz=640,
    device=0,
    save=False,
    verbose=False,
)

for index, result in enumerate(results, 1):
    image_path = Path(result.path)

    label_path = LABEL_ROOT / f"{image_path.stem}.txt"

    gt_boxes = []

    if label_path.exists():
        for line in label_path.read_text().splitlines():
            parts = line.split()

            if len(parts) != 5:
                continue

            _, xc, yc, bw, bh = map(float, parts)

            x1 = (xc - bw / 2) * 640
            y1 = (yc - bh / 2) * 640
            x2 = (xc + bw / 2) * 640
            y2 = (yc + bh / 2) * 640

            gt_boxes.append((x1, y1, x2, y2))

    for box, confidence in zip(
        result.boxes.xyxy.cpu().tolist(),
        result.boxes.conf.cpu().tolist(),
    ):
        px1, py1, px2, py2 = box

        best_iou = 0.0

        for gx1, gy1, gx2, gy2 in gt_boxes:
            ix1 = max(px1, gx1)
            iy1 = max(py1, gy1)
            ix2 = min(px2, gx2)
            iy2 = min(py2, gy2)

            iw = max(0.0, ix2 - ix1)
            ih = max(0.0, iy2 - iy1)

            intersection = iw * ih

            pred_area = max(0.0, px2 - px1) * max(0.0, py2 - py1)
            gt_area = max(0.0, gx2 - gx1) * max(0.0, gy2 - gy1)

            union = pred_area + gt_area - intersection

            if union > 0:
                iou = intersection / union
                best_iou = max(best_iou, iou)

        if best_iou == 0.0:
            rows.append([
                image_path.name,
                float(confidence),
                px1,
                py1,
                px2,
                py2,
            ])

    if index % 500 == 0:
        print(f"Processed {index}/{len(images)}")

rows.sort(key=lambda r: r[1], reverse=True)

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

with OUT_CSV.open("w", newline="") as f:
    writer = csv.writer(f)

    writer.writerow([
        "image",
        "confidence",
        "pred_x1",
        "pred_y1",
        "pred_x2",
        "pred_y2",
    ])

    writer.writerows(rows)

print()
print(f"High-confidence training background FPs: {len(rows)}")
print(f"Saved: {OUT_CSV}")
