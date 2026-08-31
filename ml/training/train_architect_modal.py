"""
Train the "Architect" - the keypoint model that finds the table's corners.

    python -m training.dataset_check ./architect_dataset --pose
    modal volume create foosgoos-architect-data
    modal volume put foosgoos-architect-data ./architect_dataset /data
    modal run training/train_architect_modal.py

    modal volume get foosgoos-architect-weights <path> ./models/table_v1.pt

WHY THIS MODEL EXISTS FOR US:

Our table is not bolted to the floor - it gets nudged most days. A fixed,
hand-clicked calibration goes stale, and stale corners mean every ball
coordinate is slightly wrong, which means goal lines drift and goals get
missed. This model re-finds the corners every few seconds so nobody has
to think about it.

You can and should ship the assisted pipeline BEFORE this exists, using
`python -m tools.calibrate_corners` and re-clicking when the table moves.
Do that first; train this when re-clicking becomes annoying.

The one thing to get right in labelling: the four keypoints must always
be placed in the SAME order - top-left, top-right, bottom-right,
bottom-left - matching config.ARCHITECT_KEYPOINTS. Get that wrong on even
some of the images and the homography comes out rotated or mirrored,
which looks like "the model is bad" but is really a labelling bug.
"""
import modal

app = modal.App("foosgoos-architect-training")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libgl1", "libglib2.0-0")
    .pip_install("ultralytics", "torch", "torchvision")
)

data_volume = modal.Volume.from_name("foosgoos-architect-data", create_if_missing=True)
weights_volume = modal.Volume.from_name("foosgoos-architect-weights", create_if_missing=True)


@app.function(
    image=image,
    gpu="A10G",
    volumes={"/data": data_volume, "/weights": weights_volume},
    timeout=60 * 60 * 3,
)
def train(epochs: int = 150, imgsz: int = 960, patience: int = 30):
    from pathlib import Path
    from ultralytics import YOLO

    data_yaml = Path("/data/data.yaml")
    if not data_yaml.exists():
        raise FileNotFoundError("/data/data.yaml is missing - upload the "
                                "unzipped Roboflow export.")
    text = data_yaml.read_text()
    print(f"--- data.yaml ---\n{text}\n-----------------")
    if "kpt_shape" not in text:
        raise ValueError(
            "This data.yaml has no kpt_shape, so it is an ordinary detection "
            "export, not a pose one. In Roboflow choose 'YOLOv8 Pose'."
        )

    # Nano is plenty: four static, high-contrast corners on a fixed
    # background is about the easiest keypoint task there is. Unlike the
    # Scout, this runs every few seconds rather than every frame, so its
    # speed barely matters - but there is nothing to gain from a bigger one.
    model = YOLO("yolov8n-pose.pt")
    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        project="/weights/runs",
        name="architect",
        patience=patience,
        degrees=5,
        translate=0.05,
        scale=0.1,
        shear=0,
        perspective=0,
        # NEVER flip: keypoint identity here is spatial. A mirrored image
        # with unmirrored labels teaches "top-left" to mean "top-right".
        fliplr=0.0,
        flipud=0.0,
        mosaic=0.0,
        hsv_v=0.3,
    )

    metrics = getattr(results, "results_dict", {}) or {}
    print("\n--- validation metrics ---")
    for key, value in metrics.items():
        if "mAP" in key or "precision" in key or "recall" in key:
            print(f"  {key:<24} {value:.4f}")
    print("\n  The number that actually matters is not mAP - it is whether "
          "the corners land in the right CORNERS. Check that with "
          "`python -m tools.watch_ball` once the weights are in place: the "
          "four table corners should read (0,0) (1,0) (1,1) (0,1).")

    best = f"{results.save_dir}/weights/best.pt"
    weights_volume.commit()
    print(f"\nBest weights (inside the volume): {best}")
    return best


@app.local_entrypoint()
def main(epochs: int = 150, imgsz: int = 960):
    path = train.remote(epochs=epochs, imgsz=imgsz)
    print("\nPull it down with:")
    print(f"  modal volume get foosgoos-architect-weights {path} ./models/table_v1.pt")
