# 🦅 Foosgoos: AI-Powered Foosball Referee & Stat Tracker

**Foosgoos** is an end-to-end hardware, machine learning, and web application stack designed to act as an automated referee and statistical tracker for foosball games. By utilizing high-speed global shutter cameras, custom YOLOv8 neural networks, and a real-time web dashboard, Foosgoos digitizes physical foosball gameplay.

---

## 🏗️ System Architecture Overview

The project is divided into three distinct operational layers:

1. **The Hardware Edge:** High-speed, uncompressed frame acquisition.
2. **The AI Backend (FastAPI):** Real-time computer vision, homography transformation, and game logic processing.
3. **The Frontend (React):** Live game dashboard and historical statistics.

---

## 💻 Part 1: The Web Application (Current State)

The software stack is a decoupled modern web application.

### Backend (Python / FastAPI)

* **Directory:** `/backend`
* **Framework:** FastAPI (Asynchronous API and Video Streaming)
* **Dependencies:** `requirements.txt` (OpenCV, Ultralytics, PyTorch, FastAPI, Uvicorn)
* **Execution:** `uvicorn main:app --reload`
* **Local URL:** `http://localhost:8000`

### Frontend (JavaScript / React)

* **Directory:** `/frontend`
* **Framework:** React (Vite-based)
* **Dependencies:** `package.json`
* **Execution:** `npm run dev`
* **Local URL:** `http://localhost:5173`

---

## 📸 Part 2: Hardware Configuration & Camera Setup

Foosball is a high-speed sport. Standard webcams suffer from "rolling shutter" (causing the ball to warp or blur into a streak) and low framerates. Foosgoos relies on specific hardware configurations to bypass these physical limitations.

### The Camera: ELP AR0234 Global Shutter

* **Sensor:** AR0234 1080p Mini UVC USB 2.0 Web PC Camera Board.
* **Lens:** 120-degree no-distortion lens.
* **Why Global Shutter:** Exposes the entire frame simultaneously, ensuring a foosball traveling at 30+ mph remains a crisp, circular object.

### The Connectivity & USB Bus

* **Requirement:** The 1080p @ 90 FPS MJPEG stream requires high bandwidth.
* **Cabling:** We utilize an **Active USB 2.0 (or 3.0) 32 ft Extension Cable** with a built-in signal repeater, terminating in a high-quality USB-C to USB-A 10Gbps data adapter into the host machine. Passive cables will cause packet drop and throttle the camera to 5 FPS.

### Lighting & Exposure Constraints (Critical)

BUT SUBJECT TO CHANGE AS WE TEST.

* **No Auto-Exposure:** Auto-exposure is strictly disabled. If the sensor is light-starved, it will lower the shutter speed, introducing motion blur and dropping the FPS.
* **Manual Override:** The camera has been tested by locking to OpenCV's Media Foundation (`CAP_MSMF`) backend with `EXPOSURE` explicitly set to `-7` (approx. $7.8\text{ ms}$ shutter speed) or `-6`.
* **Lighting Requirement:** Because the shutter is immensely fast, ambient window light is insufficient. The table might require a dedicated overhead LED light fixture to prevent frame darkening.

### Multi-Threaded Frame Acquisition

To prevent "Phantom Frames" (where the CPU processes the same frame multiple times faster than the camera can capture them), the backend utilizes a Producer-Consumer threading model. A background daemon thread constantly pulls frames from the USB bus into memory, utilizing a boolean flag to ensure the AI only processes *fresh* hardware frames, maintaining a true 90 FPS throughput.

---

## 🧠 Part 3: The Machine Learning Pipeline (The "Brain")

Foosgoos does *not* train an AI to understand "game rules" or "zones." It trains the AI to act as an eye. The pipeline uses a **Two-Model Architecture** based on **YOLOv8**.

### Model 1: "The Architect" (Keypoint Detection)

* **Goal:** Understand the physical orientation of the table.
* **Mechanism:** A YOLOv8-Pose model trained to find exactly 4 keypoints: `Top-Left`, `Top-Right`, `Bottom-Right`, `Bottom-Left` corners of the green playing surface.
* **Execution:** Runs only occasionally (at startup or if the table is bumped).
* **Output:** Generates a Perspective Transform (Homography) matrix. This flattens the angled, distorted camera view into a perfect top-down 2D grid, converting "Screen Pixels" into normalized "Table Coordinates."

### Model 2: "The Scout" (Object Detection)

* **Goal:** Track the actors on the field.
* **Mechanism:** A YOLOv8 (Small/Medium) bounding-box model.
* **Classes:** `ball`, `player_red`, `player_blue`, `player_red_two_bar`, `player_blue_two_bar`, `player_red_three_bar`, `player_blue_three_bar`, `player_red_five_bar`, `player_blue_five_bar`, `player_red_goalie_bar`, `player_blue_goalie_bar`.
* **Execution:** Runs continuously on every fresh frame (90 times a second).

### The Game Logic Layer (Math, not ML)

Once *The Scout* detects the ball at a specific pixel `(x, y)`, the backend applies the Homography matrix to map it to a flat 2D plane. Because foosball tables are standardized, "Zones" (Goalie box, 5-bar, 3-bar) are hard-coded mathematically.

* *Example:* If normalized `Ball_X < 5% of table width`, trigger a Goal event.

---

## 📊 Part 4: Data Collection & Model Training Lifecycle

To build the custom YOLOv8 weights (`best.pt`), Foosgoos follows a strict ML lifecycle.

### 1. Data Collection

Using our custom `record_dataset.py` (which implements the 90fps threading and manual exposure overrides), we extract pristine, uncompressed MJPEG frames from live gameplay and table walk-arounds.

### 2. Annotation & Feature Extraction

* **Tool:** Roboflow (or CVAT).
* **Architect Dataset:** Labeled with 4 explicit skeleton keypoints (`tl, tr, br, bl`).
* **Scout Dataset:** Bounding boxes drawn tightly around the ball (including motion blur if any) and the visible parts of the red/blue players (excluding the rods).

### 3. Splitting & Augmentation

* **Splits:** 70% Training / 20% Validation / 10% Testing.
* **Augmentation:** Applied sparingly. Slight brightness/contrast shifts to handle ambient light bleed, and small rotational changes. No extreme warping, as the camera is statically mounted.

### 4. Training (Cloud GPU via Modal)

Because local laptops lack the VRAM for rapid YOLOv8 training, we use `modal.com`.

* The dataset is uploaded to a Modal Cloud Volume.
* Training is executed on an NVIDIA A10G or H100 instance.
* Weights are exported back to the local `/backend/models/` directory for inference.

---

## 🚀 Part 5: Project Roadmap & Next Steps

1. **Hardware Finalization:** Mount the ELP camera directly above the table with the active USB extension and overhead LED lighting.
2. **Dataset Generation:** Record 100+ frames of the empty table from various angles, and 300+ frames of active gameplay.
3. **Model Training:** Annotate datasets in Roboflow and execute training via Modal to produce `table_v1.pt` and `gameplay_v1.pt`.
4. **Integration:** Embed the YOLOv8 inference engine into the FastAPI threaded camera stream.
5. **Logic Mapping:** Write the Homography and Zone-Mapping logic.
6. **Frontend Streaming:** Stream the heavily processed, AI-annotated video feed (via `StreamingResponse`) and real-time JSON stats to the React dashboard.