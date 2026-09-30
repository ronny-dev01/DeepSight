from pathlib import Path
from PIL import Image
from collections import Counter

ROOT = Path("data/derived/ghostvision_yolo/test/images")

sizes = Counter()

for path in ROOT.glob("*"):
    try:
        with Image.open(path) as im:
            sizes[im.size] += 1
    except Exception:
        pass

print("Test image dimensions")
print()

for size, count in sizes.most_common():
    print(f"{size[0]}x{size[1]} : {count}")

print()
print(f"Unique dimensions: {len(sizes)}")
