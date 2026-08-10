"""
Cloud-train the "Scout" object detector (YOLOv8) on Modal. This is
Model 2 from ARCHITECTURE.md - it tracks the ball and player rods on
every frame, 90 times a second.

ONE-TIME PREP:
  1. In Roboflow, export your Scout project as "YOLOv8".
     Unzip it locally - you'll get images/, labels/, and data.yaml.
  2. modal volume create foosgoos-scout-data
  3. modal volume put foosgoos-scout-data ./scout_dataset /data

RUN:
  modal run training/train_scout_modal.py

PULL WEIGHTS DOWN AFTER:
  modal volume get foosgoos-scout-weights <path printed below> ./models/gameplay_v1.pt
"""
import modal

app = modal.App("foosgoos-scout-training")

image = (
    modal.Image.debian_slim(python_version="3.11")
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
def train(epochs: int = 200, imgsz: int = 960, model_size: str = "s"):
    from ultralytics import YOLO

    model = YOLO(f"yolov8{model_size}.pt")  # "s" or "m" per ARCHITECTURE.md
    results = model.train(
        data="/data/data.yaml",
        epochs=epochs,
        imgsz=imgsz,
        project="/weights/runs",
        name="scout",
        patience=40,
        # Class identity (red vs. blue) is tied to physical table side
        # given your fixed camera mount - do NOT mirror-flip, or you'll
        # silently teach the model to confuse sides.
        fliplr=0.0,
        flipud=0.0,
        degrees=3,
        translate=0.05,
        scale=0.15,
        hsv_h=0.01,
        hsv_v=0.3,   # helps with ambient light bleed per ARCHITECTURE.md
        mosaic=0.5,
    )
    best = f"{results.save_dir}/weights/best.pt"
    weights_volume.commit()
    print(f"Training complete. Best weights at (inside volume): {best}")
    return best


@app.local_entrypoint()
def main(epochs: int = 200, imgsz: int = 960, model_size: str = "s"):
    path = train.remote(epochs=epochs, imgsz=imgsz, model_size=model_size)
    print("Done. Pull it locally with:")
    print(f"  modal volume get foosgoos-scout-weights {path} ./models/gameplay_v1.pt")
