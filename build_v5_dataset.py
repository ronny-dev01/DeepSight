from pathlib import Path
import shutil

BASE = Path("data/derived/ghostvision_yolo")
NEG = Path("data/derived/ghostvision_yolo_v5_hardneg")
OUT = Path("data/derived/ghostvision_yolo_v5")

SPLITS = ("train", "validation", "test")


def validate_inputs():
    """Validate every required input before creating output."""
    required_dirs = []

    for split in SPLITS:
        required_dirs.extend([
            BASE / split / "images",
            BASE / split / "labels",
        ])

    required_dirs.extend([
        NEG / "hard_negative" / "images",
        NEG / "hard_negative" / "labels",
    ])

    missing = [path for path in required_dirs if not path.is_dir()]
    if missing:
        details = "\n".join(f"  - {path}" for path in missing)
        raise FileNotFoundError(
            f"Required dataset directories are missing:\n{details}"
        )


def copy_files(source, destination):
    """Copy files without silently overwriting existing files."""
    for path in source.iterdir():
        if not path.is_file():
            continue

        target = destination / path.name
        if target.exists():
            raise FileExistsError(
                f"Refusing to overwrite existing file: {target}"
            )

        shutil.copy2(path, target)


def main():
    validate_inputs()

    # Check hard-negative filename collisions before creating output.
    for folder_name in ("images", "labels"):
        base_train = BASE / "train" / folder_name
        hard_negatives = NEG / "hard_negative" / folder_name

        conflicts = {
            path.name for path in base_train.iterdir() if path.is_file()
        } & {
            path.name for path in hard_negatives.iterdir() if path.is_file()
        }

        if conflicts:
            examples = ", ".join(sorted(conflicts)[:10])
            raise FileExistsError(
                f"Hard-negative {folder_name} filenames conflict with "
                f"training files: {examples}"
            )

    if OUT.exists():
        raise FileExistsError(
            f"Output already exists: {OUT}. "
            "Move it aside or choose a new output path. "
            "This script will not delete existing data."
        )

    created_output = False

    try:
        OUT.mkdir(parents=True)
        created_output = True

        for split in SPLITS:
            (OUT / split / "images").mkdir()
            (OUT / split / "labels").mkdir()

        for split in SPLITS:
            copy_files(
                BASE / split / "images",
                OUT / split / "images",
            )
            copy_files(
                BASE / split / "labels",
                OUT / split / "labels",
            )

        # Add hard negatives to TRAIN only.
        copy_files(
            NEG / "hard_negative" / "images",
            OUT / "train" / "images",
        )
        copy_files(
            NEG / "hard_negative" / "labels",
            OUT / "train" / "labels",
        )

    except Exception:
        # Remove only output created by this run.
        if created_output and OUT.exists():
            shutil.rmtree(OUT)
        raise

    print("v5 dataset created.")
    for split in SPLITS:
        print(
            f"{split} images:",
            len(list((OUT / split / "images").iterdir())),
        )
        print(
            f"{split} labels:",
            len(list((OUT / split / "labels").iterdir())),
        )


if __name__ == "__main__":
    main()