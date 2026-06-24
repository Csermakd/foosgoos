import time
import cv2


def interrogate_camera():
    print("Initializing Microsoft Media Foundation Pipeline...")

    # 1. Swap CAP_DSHOW for CAP_MSMF (Media Foundation handles MJPEG much better in Win 11)
    cap = cv2.VideoCapture(0, cv2.CAP_MSMF)

    # 2. Strict order of operations for MSMF
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc("M", "J", "P", "G"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cap.set(cv2.CAP_PROP_FPS, 90)

    # --- THE TRUTH SERUM ---
    # Convert the 32-bit integer FOURCC code back into human text
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
    print(f"Actually delivering: {codec_str} @ {fps} FPS ({w}x{h})\n")

    if codec_str != "MJPG":
        print("🚨 DIAGNOSTIC FAILED:")
        print(f"Windows refused MJPEG and forced the stream into '{codec_str}'.")
        print("This is why you are locked at 5 FPS. The USB 2.0 bus is choking.\n")

    prev_time = time.time()
    frames = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frames += 1
        current_time = time.time()
        elapsed = current_time - prev_time

        if elapsed > 1.0:
            print(f"True Software pull rate: {frames / elapsed:.1f} FPS")
            prev_time = current_time
            frames = 0

        cv2.imshow("Truth Serum View", cv2.resize(frame, (960, 540)))
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    interrogate_camera()