from pathlib import Path
import csv
import shutil

SRC = Path("data/derived/ghostvision_yolo_hardneg_v1")
OUT = Path("data/derived/ghostvision_yolo_v5_hardneg")

if OUT.exists():
    shutil.rmtree(OUT)

images_out = OUT / "hard_negative" / "images"
labels_out = OUT / "hard_negative" / "labels"

images_out.mkdir(parents=True)
labels_out.mkdir(parents=True)

manifest = SRC / "manifest.csv"

with open(manifest, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

rows.sort(
    key=lambda row: float(row["source_model_confidence"]),
    reverse=True
)

selected = rows[:60]

copied = 0

for row in selected:

    image_name = row["hard_negative_image"]

    src_img = SRC / "hard_negative" / "images" / image_name
    src_lbl = SRC / "hard_negative" / "labels" / (
        Path(image_name).stem + ".txt"
    )

    if not src_img.exists():
        print(f"WARNING: missing image: {image_name}")
        continue

    shutil.copy2(
        src_img,
        images_out / image_name
    )

    if src_lbl.exists():
        shutil.copy2(
            src_lbl,
            labels_out / src_lbl.name
        )
    else:
        (labels_out / (Path(image_name).stem + ".txt")).write_text(
            "",
            encoding="utf-8"
        )

    copied += 1

print(f"Source hard negatives: {len(rows)}")
print(f"Selected: {len(selected)}")
print(f"Copied images: {copied}")
print(f"Output: {OUT}")
