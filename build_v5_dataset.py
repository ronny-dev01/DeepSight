from pathlib import Path
import shutil

BASE = Path("data/derived/ghostvision_yolo")
NEG = Path("data/derived/ghostvision_yolo_v5_hardneg")
OUT = Path("data/derived/ghostvision_yolo_v5")

if OUT.exists():
    shutil.rmtree(OUT)

for split in ["train", "validation", "test"]:

    (OUT / split / "images").mkdir(parents=True)
    (OUT / split / "labels").mkdir(parents=True)

    src_images = BASE / split / "images"
    src_labels = BASE / split / "labels"

    for p in src_images.iterdir():
        if p.is_file():
            shutil.copy2(
                p,
                OUT / split / "images" / p.name
            )

    for p in src_labels.iterdir():
        if p.is_file():
            shutil.copy2(
                p,
                OUT / split / "labels" / p.name
            )

# Add only the 60 verified hard negatives to TRAIN.
neg_images = NEG / "hard_negative" / "images"
neg_labels = NEG / "hard_negative" / "labels"

for p in neg_images.iterdir():
    if p.is_file():
        shutil.copy2(
            p,
            OUT / "train" / "images" / p.name
        )

for p in neg_labels.iterdir():
    if p.is_file():
        shutil.copy2(
            p,
            OUT / "train" / "labels" / p.name
        )

print("v5 dataset created.")
print("train images:", len(list((OUT / "train" / "images").iterdir())))
print("train labels:", len(list((OUT / "train" / "labels").iterdir())))
print("validation images:", len(list((OUT / "validation" / "images").iterdir())))
print("validation labels:", len(list((OUT / "validation" / "labels").iterdir())))
print("test images:", len(list((OUT / "test" / "images").iterdir())))
print("test labels:", len(list((OUT / "test" / "labels").iterdir())))
