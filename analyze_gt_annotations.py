import csv
import os
import math
import statistics
from PIL import Image
import numpy as np

IMAGE_DIR = "data/derived/ghostvision_yolo/test/images"
LABEL_DIR = "data/derived/ghostvision_yolo/test/labels"

OUT_CSV = "runs/error_analysis/gt_annotation_consistency.csv"
OUT_TXT = "runs/error_analysis/gt_annotation_consistency_summary.txt"

rows = []

image_files = [
    f for f in os.listdir(IMAGE_DIR)
    if f.lower().endswith((".jpg", ".jpeg", ".png"))
]

image_files.sort()

missing_labels = 0
bad_labels = 0

for image_name in image_files:

    label_name = os.path.splitext(image_name)[0] + ".txt"
    label_path = os.path.join(LABEL_DIR, label_name)
    image_path = os.path.join(IMAGE_DIR, image_name)

    if not os.path.exists(label_path):
        missing_labels += 1
        continue

    image = Image.open(image_path).convert("L")
    image_np = np.asarray(image, dtype=np.float32)

    h, w = image_np.shape

    with open(label_path) as f:
        lines = [line.strip() for line in f if line.strip()]

    for obj_index, line in enumerate(lines):

        parts = line.split()

        if len(parts) != 5:
            bad_labels += 1
            continue

        try:
            cls, cx, cy, bw, bh = map(float, parts)
        except ValueError:
            bad_labels += 1
            continue

        # YOLO normalized -> pixel coordinates
        x1 = (cx - bw / 2) * w
        y1 = (cy - bh / 2) * h
        x2 = (cx + bw / 2) * w
        y2 = (cy + bh / 2) * h

        x1 = max(0, min(w - 1, x1))
        y1 = max(0, min(h - 1, y1))
        x2 = max(x1 + 1, min(w, x2))
        y2 = max(y1 + 1, min(h, y2))

        px_w = x2 - x1
        px_h = y2 - y1
        area = px_w * px_h

        aspect_ratio = px_w / px_h if px_h else 0

        # Integer crop coordinates
        ix1 = int(math.floor(x1))
        iy1 = int(math.floor(y1))
        ix2 = int(math.ceil(x2))
        iy2 = int(math.ceil(y2))

        gt = image_np[iy1:iy2, ix1:ix2]

        if gt.size == 0:
            continue

        # Context = approximately 2x GT dimensions around the GT.
        margin_x = max(px_w, 10)
        margin_y = max(px_h, 10)

        cx1 = max(0, int(math.floor(x1 - margin_x)))
        cy1 = max(0, int(math.floor(y1 - margin_y)))
        cx2 = min(w, int(math.ceil(x2 + margin_x)))
        cy2 = min(h, int(math.ceil(y2 + margin_y)))

        context = image_np[cy1:cy2, cx1:cx2]

        # Remove the GT region from the surrounding context.
        mask = np.ones(context.shape, dtype=bool)

        local_x1 = ix1 - cx1
        local_y1 = iy1 - cy1
        local_x2 = ix2 - cx1
        local_y2 = iy2 - cy1

        mask[
            max(0, local_y1):min(context.shape[0], local_y2),
            max(0, local_x1):min(context.shape[1], local_x2)
        ] = False

        surrounding = context[mask]

        if surrounding.size == 0:
            surrounding = context.flatten()

        gt_mean = float(np.mean(gt))
        gt_median = float(np.median(gt))
        gt_p90 = float(np.percentile(gt, 90))
        gt_p95 = float(np.percentile(gt, 95))
        gt_max = float(np.max(gt))

        context_mean = float(np.mean(surrounding))
        context_median = float(np.median(surrounding))
        context_p90 = float(np.percentile(surrounding, 90))
        context_p95 = float(np.percentile(surrounding, 95))

        # How much of the GT is brighter than the surrounding context's P90?
        bright_threshold = context_p90
        bright_core_fraction = float(
            np.mean(gt >= bright_threshold)
        )

        # Mean intensity difference from surrounding context.
        intensity_delta = gt_mean - context_mean

        # Relative contrast.
        intensity_contrast_ratio = (
            gt_mean / context_mean
            if context_mean > 0
            else 0
        )

        # Geometry categories.
        if bw <= 0.02:
            width_category = "very_narrow"
        elif bw <= 0.05:
            width_category = "small_width"
        elif bw >= 0.20:
            width_category = "very_wide"
        elif bw >= 0.10:
            width_category = "large_width"
        else:
            width_category = "normal_width"

        if bh <= 0.02:
            height_category = "very_short"
        elif bh <= 0.05:
            height_category = "small_height"
        elif bh >= 0.20:
            height_category = "very_tall"
        elif bh >= 0.10:
            height_category = "large_height"
        else:
            height_category = "normal_height"

        rows.append({
            "image": image_name,
            "object_index": obj_index,
            "class_id": int(cls),

            "cx_px": cx * w,
            "cy_px": cy * h,

            "width_px": px_w,
            "height_px": px_h,
            "width_norm": bw,
            "height_norm": bh,

            "area_px": area,
            "area_fraction": area / (w * h),

            "aspect_ratio": aspect_ratio,

            "gt_mean": gt_mean,
            "gt_median": gt_median,
            "gt_p90": gt_p90,
            "gt_p95": gt_p95,
            "gt_max": gt_max,

            "context_mean": context_mean,
            "context_median": context_median,
            "context_p90": context_p90,
            "context_p95": context_p95,

            "bright_core_fraction": bright_core_fraction,
            "intensity_delta": intensity_delta,
            "intensity_contrast_ratio": intensity_contrast_ratio,

            "width_category": width_category,
            "height_category": height_category,
        })

# Save per-object CSV.
os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)

fieldnames = list(rows[0].keys())

with open(OUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

def values(key):
    return [float(r[key]) for r in rows]

def percentile(data, p):
    return float(np.percentile(data, p))

def fmt_stats(data):
    return (
        f"mean={statistics.mean(data):.4f}, "
        f"median={statistics.median(data):.4f}, "
        f"P10={percentile(data,10):.4f}, "
        f"P90={percentile(data,90):.4f}"
    )

widths = values("width_norm")
heights = values("height_norm")
areas = values("area_fraction")
aspect = values("aspect_ratio")
bright = values("bright_core_fraction")
contrast = values("intensity_contrast_ratio")
delta = values("intensity_delta")

very_narrow = sum(r["width_norm"] <= 0.02 for r in rows)
small_width = sum(0.02 < r["width_norm"] <= 0.05 for r in rows)
very_wide = sum(r["width_norm"] >= 0.20 for r in rows)

very_short = sum(r["height_norm"] <= 0.02 for r in rows)
small_height = sum(0.02 < r["height_norm"] <= 0.05 for r in rows)
very_tall = sum(r["height_norm"] >= 0.20 for r in rows)

bright_lt25 = sum(r["bright_core_fraction"] < 0.25 for r in rows)
bright_25_50 = sum(
    0.25 <= r["bright_core_fraction"] < 0.50
    for r in rows
)
bright_50_75 = sum(
    0.50 <= r["bright_core_fraction"] < 0.75
    for r in rows
)
bright_ge75 = sum(
    r["bright_core_fraction"] >= 0.75
    for r in rows
)

# Highest / lowest representative cases.
bright_sorted = sorted(
    rows,
    key=lambda r: r["bright_core_fraction"]
)

contrast_sorted = sorted(
    rows,
    key=lambda r: r["intensity_contrast_ratio"],
    reverse=True
)

aspect_sorted = sorted(
    rows,
    key=lambda r: r["aspect_ratio"]
)

with open(OUT_TXT, "w") as f:

    f.write("GHOSTVISION V1 - GT ANNOTATION CONSISTENCY AUDIT\n")
    f.write("=" * 60 + "\n\n")

    f.write(f"Images scanned: {len(image_files)}\n")
    f.write(f"GT objects analyzed: {len(rows)}\n")
    f.write(f"Missing labels: {missing_labels}\n")
    f.write(f"Malformed labels: {bad_labels}\n\n")

    f.write("GEOMETRY\n")
    f.write("-" * 60 + "\n")
    f.write(f"Width normalized:       {fmt_stats(widths)}\n")
    f.write(f"Height normalized:      {fmt_stats(heights)}\n")
    f.write(f"Area fraction:          {fmt_stats(areas)}\n")
    f.write(f"Aspect ratio W/H:       {fmt_stats(aspect)}\n\n")

    f.write("WIDTH CATEGORIES\n")
    f.write("-" * 60 + "\n")
    f.write(f"Very narrow <=2%:       {very_narrow}\n")
    f.write(f"Small 2-5%:             {small_width}\n")
    f.write(f"Very wide >=20%:        {very_wide}\n\n")

    f.write("HEIGHT CATEGORIES\n")
    f.write("-" * 60 + "\n")
    f.write(f"Very short <=2%:        {very_short}\n")
    f.write(f"Small 2-5%:             {small_height}\n")
    f.write(f"Very tall >=20%:        {very_tall}\n\n")

    f.write("BRIGHT-CORE OCCUPANCY\n")
    f.write("-" * 60 + "\n")
    f.write(
        "Definition: fraction of GT pixels whose intensity is at or above\n"
        "the P90 intensity of the surrounding context.\n\n"
    )
    f.write(f"Overall:                 {fmt_stats(bright)}\n")
    f.write(f"<25%:                    {bright_lt25}\n")
    f.write(f"25-50%:                  {bright_25_50}\n")
    f.write(f"50-75%:                  {bright_50_75}\n")
    f.write(f">=75%:                   {bright_ge75}\n\n")

    f.write("INTENSITY CONTRAST\n")
    f.write("-" * 60 + "\n")
    f.write(
        "GT mean / surrounding mean:\n"
        f"{fmt_stats(contrast)}\n"
    )
    f.write(
        "GT mean - surrounding mean:\n"
        f"{fmt_stats(delta)}\n\n"
    )

    f.write("LOWEST BRIGHT-CORE CASES\n")
    f.write("-" * 60 + "\n")

    for r in bright_sorted[:10]:
        f.write(
            f"{r['bright_core_fraction']:.3f} | "
            f"contrast={r['intensity_contrast_ratio']:.3f} | "
            f"W={r['width_norm']:.3f} | "
            f"H={r['height_norm']:.3f} | "
            f"{r['image']}#{r['object_index']}\n"
        )

    f.write("\nHIGHEST CONTRAST CASES\n")
    f.write("-" * 60 + "\n")

    for r in contrast_sorted[:10]:
        f.write(
            f"{r['intensity_contrast_ratio']:.3f} | "
            f"bright_core={r['bright_core_fraction']:.3f} | "
            f"W={r['width_norm']:.3f} | "
            f"H={r['height_norm']:.3f} | "
            f"{r['image']}#{r['object_index']}\n"
        )

    f.write("\nMOST EXTREME ASPECT RATIOS\n")
    f.write("-" * 60 + "\n")

    for r in aspect_sorted[:5]:
        f.write(
            f"AR={r['aspect_ratio']:.3f} | "
            f"W={r['width_norm']:.3f} | "
            f"H={r['height_norm']:.3f} | "
            f"{r['image']}#{r['object_index']}\n"
        )

    f.write("\n")

print("GT annotation audit complete.")
print()
print(f"Images scanned:       {len(image_files)}")
print(f"GT objects analyzed:  {len(rows)}")
print(f"Missing labels:       {missing_labels}")
print(f"Malformed labels:     {bad_labels}")
print()
print("Generated:")
print(f"  {OUT_CSV}")
print(f"  {OUT_TXT}")
print()
print("Geometry:")
print(f"  Width median:       {statistics.median(widths):.4f}")
print(f"  Height median:      {statistics.median(heights):.4f}")
print(f"  Area median:        {statistics.median(areas):.6f}")
print(f"  Aspect median:      {statistics.median(aspect):.4f}")
print()
print("Bright-core:")
print(f"  Median occupancy:   {statistics.median(bright):.4f}")
print(f"  <25%:               {bright_lt25}")
print(f"  25-50%:             {bright_25_50}")
print(f"  50-75%:             {bright_50_75}")
print(f"  >=75%:              {bright_ge75}")
print()
print("Intensity:")
print(f"  Median contrast:    {statistics.median(contrast):.4f}")
print(f"  Median delta:       {statistics.median(delta):.4f}")

