import time
import cv2


def interrogate_camera():
    print("Initializing Microsoft Media Foundation Pipeline...")

    # 1. Targeting the external ELP camera (Index 1) via Media Foundation
    # (If it crashes instantly, change the '1' to a '2')
    cap = cv2.VideoCapture(1, cv2.CAP_MSMF)

    # 2. Strict order of operations for high-speed USB bus
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc("M", "J", "P", "G"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cap.set(cv2.CAP_PROP_FPS, 90)

    # ================= THE PHYSICAL OVERRIDE =================
    # Break the "Global Shutter Light-Starvation Trap"
    # 0.25 in Media Foundation maps to "Manual Exposure Mode"
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)

    # Force shutter speed fast (-6 is ~1/64th sec, -7 is ~1/128th sec)
    # If the video pops up PITCH BLACK, change this to -5 or -4.
    cap.set(cv2.CAP_PROP_EXPOSURE, -6)
    # =========================================================

    # --- THE TRUTH SERUM ---
    fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
    codec_str = (
        chr(fourcc_int & 0xFF)
        + chr((fourcc_int >> 8) & 0xFF)
        + chr((fourcc_int >> 16) & 0xFF)
        + chr((fourcc_int >> 24) & 0xFF)
    )

    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"\nTarget requested : MJPG @ 90 FPS")
    print(f"Actually delivering: '{codec_str}' @ {fps} FPS ({w}x{h})\n")

    if codec_str != "MJPG":
        print("🚨 DIAGNOSTIC FAILED:")
        print(f"Windows refused MJPEG and forced the stream into '{codec_str}'.")
        print("The USB bus is choking. Try a different physical USB port.\n")

    prev_time = time.time()
    frames = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame from Index 1. (Is the camera plugged in?)")
            break

        frames += 1
        current_time = time.time()
        elapsed = current_time - prev_time

        if elapsed > 1.0:
            print(f"True Software pull rate: {frames / elapsed:.1f} FPS")
            prev_time = current_time
            frames = 0

        # Downscale just for your laptop screen preview
        cv2.imshow("Truth Serum View (ELP AR0234)", cv2.resize(frame, (960, 540)))

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    interrogate_camera()