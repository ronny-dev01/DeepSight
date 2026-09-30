import csv
from pathlib import Path
from ultralytics import YOLO

MODEL = "runs/detect/runs/train/ghostvision_crabpot_v5_finetune_hardneg-2/weights/best.pt"
IMAGE_DIR = "data/derived/ghostvision_yolo/test/images"
OUT = Path("runs/error_analysis/ghostvision_crabpot_v5_raw_predictions.csv")

model = YOLO(MODEL)

rows = []

results = model.predict(
    source=IMAGE_DIR,
    conf=0.001,
    iou=0.45,
    imgsz=640,
    device=0,
    save=False,
    verbose=False,
)

for result in results:
    image_name = Path(result.path).name

    if result.boxes is None:
        continue

    boxes = result.boxes

    for i in range(len(boxes)):
        xyxy = boxes.xyxy[i].tolist()
        conf = float(boxes.conf[i])

        rows.append([
            image_name,
            conf,
            xyxy[0],
            xyxy[1],
            xyxy[2],
            xyxy[3],
        ])

OUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUT, "w", newline="", encoding="utf-8") as f:
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

print(f"Images: {len(results)}")
print(f"Predictions: {len(rows)}")
print(f"Saved: {OUT}")
