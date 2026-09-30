from pathlib import Path
import csv
import random
from PIL import Image, ImageOps

CSV_PATH = Path("runs/error_analysis/v1_train_background_fps.csv")
IMAGE_ROOT = Path("data/derived/ghostvision_yolo/train/images")
LABEL_ROOT = Path("data/derived/ghostvision_yolo/train/labels")

OUT_ROOT = Path("data/derived/ghostvision_yolo_hardneg_v1")
OUT_IMAGES = OUT_ROOT / "hard_negative" / "images"
OUT_LABELS = OUT_ROOT / "hard_negative" / "labels"
MANIFEST = OUT_ROOT / "manifest.csv"

OUT_IMAGES.mkdir(parents=True, exist_ok=True)
OUT_LABELS.mkdir(parents=True, exist_ok=True)

random.seed(42)

rows = list(csv.DictReader(CSV_PATH.open(newline="")))

safe = []

for row in rows:
    confidence = float(row["confidence"])

    image_path = IMAGE_ROOT / row["image"]
    label_path = LABEL_ROOT / f"{image_path.stem}.txt"

    with Image.open(image_path) as im:
        w, h = im.size

    x1 = float(row["pred_x1"])
    y1 = float(row["pred_y1"])
    x2 = float(row["pred_x2"])
    y2 = float(row["pred_y2"])

    bw = x2 - x1
    bh = y2 - y1

    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2

    half_w = max(bw * 1.5, 40)
    half_h = max(bh * 1.5, 40)

    crop_x1 = max(0, cx - half_w)
    crop_y1 = max(0, cy - half_h)
    crop_x2 = min(w, cx + half_w)
    crop_y2 = min(h, cy + half_h)

    intersects_gt = False

    if label_path.exists():
        for line in label_path.read_text().splitlines():
            parts = line.split()

            if len(parts) != 5:
                continue

            _, xc, yc, gbw, gbh = map(float, parts)

            gx1 = (xc - gbw / 2) * 640
            gy1 = (yc - gbh / 2) * 640
            gx2 = (xc + gbw / 2) * 640
            gy2 = (yc + gbh / 2) * 640

            ix1 = max(crop_x1, gx1)
            iy1 = max(crop_y1, gy1)
            ix2 = min(crop_x2, gx2)
            iy2 = min(crop_y2, gy2)

            if ix2 > ix1 and iy2 > iy1:
                intersects_gt = True
                break

    if not intersects_gt:
        row["_confidence"] = confidence
        safe.append(row)

# One candidate per source image.
by_image = {}

for row in safe:
    image = row["image"]

    if image not in by_image:
        by_image[image] = row
    elif float(row["confidence"]) > float(by_image[image]["confidence"]):
        by_image[image] = row

unique = list(by_image.values())

high = [
    r for r in unique
    if float(r["confidence"]) >= 0.40
]

medium = [
    r for r in unique
    if 0.30 <= float(r["confidence"]) < 0.40
]

high.sort(key=lambda r: float(r["confidence"]), reverse=True)
medium.sort(key=lambda r: float(r["confidence"]), reverse=True)

selected = high[:97]

random.shuffle(medium)
selected.extend(medium[:80])

selected.sort(key=lambda r: float(r["confidence"]), reverse=True)

print(f"Safe unique candidates: {len(unique)}")
print(f"Selected hard negatives: {len(selected)}")
print(f"  >= 0.40 confidence: {len([r for r in selected if float(r['confidence']) >= 0.40])}")
print(f"  0.30-0.40 confidence: {len([r for r in selected if float(r['confidence']) < 0.40])}")

manifest_rows = []

for index, row in enumerate(selected, 1):
    source = IMAGE_ROOT / row["image"]

    with Image.open(source).convert("RGB") as im:
        w, h = im.size

        x1 = float(row["pred_x1"])
        y1 = float(row["pred_y1"])
        x2 = float(row["pred_x2"])
        y2 = float(row["pred_y2"])

        bw = x2 - x1
        bh = y2 - y1

        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2

        half_w = max(bw * 1.5, 40)
        half_h = max(bh * 1.5, 40)

        left = max(0, int(cx - half_w))
        top = max(0, int(cy - half_h))
        right = min(w, int(cx + half_w))
        bottom = min(h, int(cy + half_h))

        crop = im.crop((left, top, right, bottom))

        # Preserve aspect ratio and pad to 640x640.
        crop = ImageOps.contain(crop, (640, 640))
        canvas = Image.new("RGB", (640, 640), (114, 114, 114))

        paste_x = (640 - crop.width) // 2
        paste_y = (640 - crop.height) // 2

        canvas.paste(crop, (paste_x, paste_y))

        output_name = f"hardneg_{index:04d}_{Path(row['image']).stem}.jpg"

        image_out = OUT_IMAGES / output_name
        label_out = OUT_LABELS / f"{Path(output_name).stem}.txt"

        canvas.save(image_out, quality=95)

        # Empty YOLO label = verified background image.
        label_out.write_text("")

        manifest_rows.append([
            output_name,
            row["image"],
            f"{float(row['confidence']):.8f}",
        ])

with MANIFEST.open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "hard_negative_image",
        "source_image",
        "source_model_confidence",
    ])
    writer.writerows(manifest_rows)

print()
print(f"Images written: {len(manifest_rows)}")
print(f"Labels written: {len(manifest_rows)}")
print(f"Output: {OUT_ROOT}")
