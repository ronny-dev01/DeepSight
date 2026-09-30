from pathlib import Path
import csv
from collections import Counter
from PIL import Image

CSV_PATH = Path("runs/error_analysis/v1_train_background_fps.csv")
IMAGE_ROOT = Path("data/derived/ghostvision_yolo/train/images")
LABEL_ROOT = Path("data/derived/ghostvision_yolo/train/labels")

rows = list(csv.DictReader(CSV_PATH.open(newline="")))

print(f"Candidates: {len(rows)}")

# ---------------------------------------------------------
# Image dimensions
# ---------------------------------------------------------

dimensions = Counter()

for row in rows:
    path = IMAGE_ROOT / row["image"]
    with Image.open(path) as im:
        dimensions[im.size] += 1

print()
print("Candidate image dimensions")
print("-" * 40)

for dimension, count in dimensions.items():
    print(f"{dimension}: {count}")

# ---------------------------------------------------------
# Confidence distribution
# ---------------------------------------------------------

bins = [
    ("0.30-0.35", 0.30, 0.35),
    ("0.35-0.40", 0.35, 0.40),
    ("0.40-0.45", 0.40, 0.45),
    ("0.45-0.50", 0.45, 0.50),
    ("0.50-0.55", 0.50, 0.55),
    ("0.55+", 0.55, float("inf")),
]

print()
print("Confidence distribution")
print("-" * 55)

for name, low, high in bins:
    values = [
        float(r["confidence"])
        for r in rows
        if low <= float(r["confidence"]) < high
    ]

    print(
        f"{name:>10}  "
        f"count={len(values):4d}  "
        f"percent={len(values) / len(rows) * 100:6.2f}%"
        if values
        else
        f"{name:>10}  count=   0"
    )

# ---------------------------------------------------------
# Unique images / repeated candidates
# ---------------------------------------------------------

per_image = Counter(r["image"] for r in rows)

print()
print(f"Unique images containing candidates: {len(per_image)}")
print(f"Average candidates per candidate-image: {len(rows) / len(per_image):.2f}")
print(f"Maximum candidates in one image: {max(per_image.values())}")

print()
print("Images with most candidates")
print("-" * 70)

for image, count in per_image.most_common(20):
    max_conf = max(
        float(r["confidence"])
        for r in rows
        if r["image"] == image
    )

    print(
        f"{count:3d} candidates  "
        f"max_conf={max_conf:.4f}  "
        f"{image}"
    )

# ---------------------------------------------------------
# Check whether candidate crop context contains GT
#
# We use a 3x prediction-box context, matching the crop
# strategy we will use for the hard-negative dataset.
# ---------------------------------------------------------

safe = []
unsafe = []

for row in rows:
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

    if intersects_gt:
        unsafe.append(row)
    else:
        safe.append(row)

print()
print("Crop safety audit")
print("-" * 55)
print(f"Safe background crops:   {len(safe)}")
print(f"Unsafe crops:             {len(unsafe)}")
print(f"Safe percentage:          {len(safe) / len(rows) * 100:.2f}%")

print()
print("Highest-confidence SAFE candidates")
print("-" * 90)

safe_sorted = sorted(
    safe,
    key=lambda r: float(r["confidence"]),
    reverse=True,
)

for i, row in enumerate(safe_sorted[:30], 1):
    print(
        f"{i:2d}. "
        f"conf={float(row['confidence']):.4f}  "
        f"{row['image']}"
    )
