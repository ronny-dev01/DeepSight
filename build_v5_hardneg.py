
from pathlib import Path
import csv
import shutil

SRC = Path("data/derived/ghostvision_yolo_hardneg_v1")
OUT = Path("data/derived/ghostvision_yolo_v5_hardneg")
MANIFEST = SRC / "manifest.csv"

REQUIRED_COLUMNS = {
    "source_model_confidence",
    "hard_negative_image",
}


def main():
    # Validate all prerequisites before creating output.
    if not MANIFEST.is_file():
        raise FileNotFoundError(
            f"Hard-negative manifest not found: {MANIFEST}"
        )

    if OUT.exists():
        raise FileExistsError(
            f"Output already exists: {OUT}. "
            "Move it aside or choose a new output path; "
            "this script will not delete existing data."
        )

    with MANIFEST.open(
        newline="",
        encoding="utf-8-sig",
    ) as f:
        reader = csv.DictReader(f)

        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"Manifest is missing required columns: {sorted(missing)}"
            )

        rows = list(reader)

    try:
        rows.sort(
            key=lambda row: float(row["source_model_confidence"]),
            reverse=True,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Manifest contains an invalid source_model_confidence value."
        ) from exc

    selected = rows[:60]
    images_out = OUT / "hard_negative" / "images"
    labels_out = OUT / "hard_negative" / "labels"

    copied = 0
    missing_images = []
    created_output = False

    try:
        images_out.mkdir(parents=True)
        created_output = True
        labels_out.mkdir(parents=True)

        for row in selected:
            image_name = row["hard_negative_image"].strip()
            if not image_name or Path(image_name).name != image_name:
                raise ValueError(
                    f"Invalid hard_negative_image filename: {image_name!r}"
                )

            src_img = SRC / "hard_negative" / "images" / image_name
            src_lbl = (
                SRC / "hard_negative" / "labels"
                / f"{Path(image_name).stem}.txt"
            )

            if not src_img.is_file():
                missing_images.append(image_name)
                continue

            shutil.copy2(src_img, images_out / image_name)

            if src_lbl.is_file():
                shutil.copy2(src_lbl, labels_out / src_lbl.name)
            else:
                (labels_out / f"{Path(image_name).stem}.txt").write_text(
                    "",
                    encoding="utf-8",
                )

            copied += 1

    except Exception:
        # Remove output only if this run created it.
        if created_output and OUT.exists():
            shutil.rmtree(OUT)
        raise

    print(f"Source hard negatives: {len(rows)}")
    print(f"Selected: {len(selected)}")
    print(f"Copied images: {copied}")
    print(f"Missing images: {len(missing_images)}")
    for name in missing_images:
        print(f"WARNING: missing image: {name}")
    print(f"Output: {OUT}")


if __name__ == "__main__":
    main()
