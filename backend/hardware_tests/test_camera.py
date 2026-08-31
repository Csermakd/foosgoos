import cv2
import time

def test_high_speed_cam():
    # 0 is usually your laptop webcam. 1 or 2 is usually the external USB camera.
    # If 1 doesn't work, change it to 0 or 2.
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW) # CAP_DSHOW is recommended for Windows

    # --- THE CRITICAL SETTINGS ---
    # You MUST set FOURCC to MJPG before setting resolution/FPS
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    
    # Set to 1080p
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    # Request 90 FPS
    cap.set(cv2.CAP_PROP_FPS, 90)

    # Verify what OpenCV actually negotiated with the hardware
    actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Hardware Negotiated: {actual_width}x{actual_height} @ {actual_fps} FPS")

    prev_time = time.time()
    frames = 0

    print("Press 'q' to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # Calculate actual software FPS
        frames += 1
        current_time = time.time()
        elapsed = current_time - prev_time
        
        if elapsed > 1.0:
            software_fps = frames / elapsed
            print(f"Actual Software Processing Speed: {software_fps:.1f} FPS")
            prev_time = current_time
            frames = 0

        # Resize for display so it fits on your laptop screen
        display_frame = cv2.resize(frame, (960, 540))
        cv2.imshow("ELP 90FPS Test", display_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_high_speed_cam()