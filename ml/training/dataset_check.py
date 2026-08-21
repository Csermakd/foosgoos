"""
Sanity-check a Roboflow export before spending GPU time on it.

    python -m training.dataset_check ./scout_dataset
    python -m training.dataset_check ./architect_dataset --pose

Almost every "the model came out useless" story is really a dataset
problem that was visible in thirty seconds: an empty split, a class list
that does not match what the code expects, images with no labels at all,
or a train/val split so small the validation number is noise.

Run this before `modal volume put`. It is much cheaper to find out here.
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}


def read_yaml(path):
    """Minimal YAML reader - enough for a data.yaml, no PyYAML needed."""
    data, key = {}, None
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.lstrip().startswith("- ") and key:
            data.setdefault(key, [])
            if isinstance(data[key], list):
                data[key].append(line.lstrip()[2:].strip().strip("'\""))
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            key, value = key.strip(), value.strip()
            if value.startswith("[") and value.endswith("]"):
                data[key] = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
            elif value:
                data[key] = value.strip("'\"")
            else:
                data[key] = []
    return data


def split_dirs(root, spec):
    """Resolve a data.yaml path entry to (images_dir, labels_dir)."""
    if not spec:
        return None, None
    candidate = (root / str(spec).lstrip("./")).resolve()
    if candidate.name != "images" and (candidate / "images").exists():
        candidate = candidate / "images"
    labels = Path(str(candidate).replace("/images", "/labels"))
    return candidate, labels


def check_split(name, images_dir, labels_dir, expect_pose, problems, warnings):
    if images_dir is None or not images_dir.exists():
        problems.append(f"{name}: images directory missing ({images_dir})")
        return 0, Counter()

    images = [p for p in images_dir.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES]
    if not images:
        problems.append(f"{name}: no images found in {images_dir}")
        return 0, Counter()

    class_counts = Counter()
    unlabelled = 0
    bad_rows = 0
    for image in images:
        label = labels_dir / (image.stem + ".txt")
        if not label.exists() or not label.read_text().strip():
            unlabelled += 1
            continue
        for row in label.read_text().splitlines():
            parts = row.split()
            if not parts:
                continue
            class_counts[int(float(parts[0]))] += 1
            # detect: cls cx cy w h (5). pose adds 2 or 3 numbers per keypoint.
            if not expect_pose and len(parts) != 5:
                bad_rows += 1
            coords = [float(v) for v in parts[1:5]] if len(parts) >= 5 else []
            if any(not (-0.01 <= c <= 1.01) for c in coords):
                bad_rows += 1

    if unlabelled:
        share = unlabelled / len(images)
        message = (f"{name}: {unlabelled}/{len(images)} images have no labels")
        # Some empty frames are GOOD - they teach the model what "no ball"
        # looks like. A majority being empty means you forgot to label.
        (problems if share > 0.5 else warnings).append(
            message + (" - did you export before finishing?" if share > 0.5
                       else " (a few negatives are healthy)")
        )
    if bad_rows:
        problems.append(f"{name}: {bad_rows} label rows are malformed or "
                        f"out of the 0-1 range")
    return len(images), class_counts


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dataset", help="folder holding the unzipped Roboflow export")
    parser.add_argument("--pose", action="store_true",
                        help="this is the Architect (keypoint) dataset")
    args = parser.parse_args()

    root = Path(args.dataset).resolve()
    yaml_path = root / "data.yaml"
    if not yaml_path.exists():
        raise SystemExit(f"No data.yaml in {root}. Point this at the folder "
                         f"you unzipped the Roboflow export into.")

    data = read_yaml(yaml_path)
    names = data.get("names") or []
    problems, warnings = [], []

    print(f"dataset:  {root}")
    print(f"classes:  {names}")

    if args.pose:
        shape = data.get("kpt_shape")
        print(f"kpt_shape: {shape}")
        if not shape:
            problems.append("data.yaml has no kpt_shape - this is not a "
                            "YOLOv8 *Pose* export. Re-export as 'YOLOv8 Pose'.")
        elif str(shape).replace(" ", "").startswith("[4"):
            pass
        else:
            problems.append(f"kpt_shape is {shape}, expected 4 keypoints "
                            f"(the four table corners)")

    totals = Counter()
    sizes = {}
    for split in ("train", "val", "test"):
        images_dir, labels_dir = split_dirs(root, data.get(split))
        if data.get(split) is None and split == "test":
            continue
        count, class_counts = check_split(split, images_dir, labels_dir,
                                          args.pose, problems, warnings)
        sizes[split] = count
        totals.update(class_counts)
        distribution = ", ".join(f"{names[i] if i < len(names) else i}={n}"
                                 for i, n in sorted(class_counts.items()))
        print(f"  {split:<6} {count:>5} images   {distribution or '(no labels)'}")

    train_n = sizes.get("train", 0)
    if train_n < 100:
        warnings.append(f"only {train_n} training images - expect a fragile "
                        f"model. 300+ varied frames is the target.")
    if sizes.get("val", 0) < 20:
        warnings.append(f"only {sizes.get('val', 0)} validation images - the "
                        f"mAP number will be mostly noise.")

    for class_id, count in totals.items():
        if count < 50:
            label = names[class_id] if class_id < len(names) else class_id
            warnings.append(f"class '{label}' has only {count} instances - "
                            f"it will be detected poorly.")

    print()
    for w in warnings:
        print(f"  WARN   {w}")
    for p in problems:
        print(f"  ERROR  {p}")
    if not problems and not warnings:
        print("  looks good.")
    print()
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
