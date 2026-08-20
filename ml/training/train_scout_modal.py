"""
Train the "Scout" - the ball detector that runs on every frame.

    python -m training.dataset_check ./scout_dataset     # ALWAYS do this first
    modal volume create foosgoos-scout-data
    modal volume put foosgoos-scout-data ./scout_dataset /data
    modal run training/train_scout_modal.py

    # then pull the weights down with the command it prints
    modal volume get foosgoos-scout-weights <path> ./models/gameplay_v1.pt

DEFAULTS AND WHY:

  model_size "n" (nano), not "s". This model runs on EVERY frame, up to 90
  times a second, on whatever machine is bolted to the table. A bigger
  model that makes inference run at 12fps is worse than a slightly less
  accurate one at 60fps, because a ball moving 15cm per frame can cross
  the entire goal between two processed frames. Measure your real fps
  before reaching for "s" or "m".

  imgsz 640, not 960. Same argument. Go up only if you can show the ball
  is being missed at 640 - it is a large, high-contrast object.

  fliplr / flipud = 0. Mirroring would swap which end of the table is
  which. With a single 'ball' class that is harmless today, but the moment
  you add player_red / player_blue it would actively teach the model to
  confuse the teams, so it stays off.

  mosaic 0.5. Tiles four images together, which helps the model handle
  the ball appearing anywhere in frame. Ultralytics disables it for the
  last few epochs by itself.
"""
import modal

app = modal.App("foosgoos-scout-training")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libgl1", "libglib2.0-0")   # OpenCV's runtime deps
    .pip_install("ultralytics", "torch", "torchvision")
)

data_volume = modal.Volume.from_name("foosgoos-scout-data", create_if_missing=True)
weights_volume = modal.Volume.from_name("foosgoos-scout-weights", create_if_missing=True)


@app.function(
    image=image,
    gpu="A10G",
    volumes={"/data": data_volume, "/weights": weights_volume},
    timeout=60 * 60 * 4,
)
def train(epochs: int = 200, imgsz: int = 640, model_size: str = "n",
          patience: int = 40):
    from pathlib import Path
    from ultralytics import YOLO

    data_yaml = Path("/data/data.yaml")
    if not data_yaml.exists():
        raise FileNotFoundError(
            "/data/data.yaml is missing. The volume should contain the "
            "UNZIPPED Roboflow export (images/, labels/, data.yaml), not the "
            "zip itself."
        )
    print(f"--- data.yaml ---\n{data_yaml.read_text()}\n-----------------")

    model = YOLO(f"yolov8{model_size}.pt")
    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        project="/weights/runs",
        name="scout",
        patience=patience,
        # Light augmentation: the camera is fixed above the table, so
        # heavy geometric warping teaches situations that never occur.
        degrees=3,
        translate=0.05,
        scale=0.15,
        shear=0,
        perspective=0,
        fliplr=0.0,
        flipud=0.0,
        hsv_h=0.01,
        hsv_s=0.4,
        hsv_v=0.4,     # ambient light varies a lot through the day
        mosaic=0.5,
    )

    metrics = getattr(results, "results_dict", {}) or {}
    print("\n--- validation metrics ---")
    for key in ("metrics/precision(B)", "metrics/recall(B)",
                "metrics/mAP50(B)", "metrics/mAP50-95(B)"):
        if key in metrics:
            print(f"  {key:<22} {metrics[key]:.4f}")
    map50 = metrics.get("metrics/mAP50(B)")
    if map50 is not None:
        if map50 < 0.8:
            print("\n  mAP50 below 0.80 for a single large high-contrast "
                  "object usually means the LABELS are inconsistent, not that "
                  "the model is too small. Re-check the dataset before "
                  "training longer or bigger.")
        else:
            print(f"\n  mAP50 {map50:.3f} - good. What matters next is how it "
                  f"does on FAST, BLURRED balls, which this number barely "
                  f"reflects. Run evaluation/evaluate_goals.py on real footage.")

    best = f"{results.save_dir}/weights/best.pt"
    weights_volume.commit()
    print(f"\nBest weights (inside the volume): {best}")
    return best


@app.local_entrypoint()
def main(epochs: int = 200, imgsz: int = 640, model_size: str = "n"):
    path = train.remote(epochs=epochs, imgsz=imgsz, model_size=model_size)
    print("\nPull it down with:")
    print(f"  modal volume get foosgoos-scout-weights {path} ./models/gameplay_v1.pt")
