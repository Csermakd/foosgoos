"""
Cloud-train the "Architect" keypoint model (YOLOv8-Pose) on Modal.
This is Model 1 from ARCHITECTURE.md - it finds the 4 table corners
(top_left, top_right, bottom_right, bottom_left) used to build the
Homography matrix.

ONE-TIME PREP:
  1. In Roboflow, export your Architect project as "YOLOv8 (Pose)".
     Unzip it locally - you'll get an images/, labels/, and data.yaml.
  2. modal volume create foosgoos-architect-data
  3. modal volume put foosgoos-architect-data ./architect_dataset /data

RUN:
  modal run training/train_architect_modal.py

PULL WEIGHTS DOWN AFTER:
  modal volume get foosgoos-architect-weights <path printed below> ./models/table_v1.pt
"""
import modal

app = modal.App("foosgoos-architect-training")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("ultralytics", "torch", "torchvision")
)

data_volume = modal.Volume.from_name("foosgoos-architect-data", create_if_missing=True)
weights_volume = modal.Volume.from_name("foosgoos-architect-weights", create_if_missing=True)


@app.function(
    image=image,
    gpu="A10G",       # bump to "H100" if you want it, per ARCHITECTURE.md
    volumes={"/data": data_volume, "/weights": weights_volume},
    timeout=60 * 60 * 3,
)
def train(epochs: int = 150, imgsz: int = 960):
    from ultralytics import YOLO

    model = YOLO("yolov8n-pose.pt")  # nano is plenty for 4 static keypoints
    results = model.train(
        data="/data/data.yaml",
        epochs=epochs,
        imgsz=imgsz,
        project="/weights/runs",
        name="architect",
        patience=30,
        # Sparse augmentation per ARCHITECTURE.md Part 4 - the camera is
        # statically mounted, so keep transforms small and realistic.
        degrees=5,
        translate=0.05,
        scale=0.1,
        shear=0,
        perspective=0,
        fliplr=0.0,   # do NOT flip - keypoint order is spatial (tl/tr/br/bl)
        mosaic=0.0,
    )
    best = f"{results.save_dir}/weights/best.pt"
    weights_volume.commit()
    print(f"Training complete. Best weights at (inside volume): {best}")
    return best


@app.local_entrypoint()
def main(epochs: int = 150, imgsz: int = 960):
    path = train.remote(epochs=epochs, imgsz=imgsz)
    print("Done. Pull it locally with:")
    print(f"  modal volume get foosgoos-architect-weights {path} ./models/table_v1.pt")
