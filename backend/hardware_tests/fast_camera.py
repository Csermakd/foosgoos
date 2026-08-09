import os
import time
import cv2
from threading import Thread

os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"

class CameraStream:
    def __init__(self, src=1):
        # Initialize the camera
        self.cap = cv2.VideoCapture(src, cv2.CAP_MSMF)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc("M", "J", "P", "G"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.cap.set(cv2.CAP_PROP_FPS, 90)
        
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
        self.cap.set(cv2.CAP_PROP_EXPOSURE, -5) 
        
        # Read the first frame
        self.ret, self.frame = self.cap.read()
        self.stopped = False

    def start(self):
        # Start a dedicated background thread to read frames
        Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            self.ret, self.frame = self.cap.read()

    def read(self):
        # Main thread simply grabs the most recent frame
        return self.frame

    def stop(self):
        self.stopped = True
        self.cap.release()

if __name__ == "__main__":
    print("Starting Multi-Threaded Camera Stream...")
    
    # Initialize and start the background thread
    stream = CameraStream(src=1).start()
    time.sleep(1.0) # Let the hardware warm up

    frames = 0
    prev_time = time.time()

    while True:
        frame = stream.read()
        if frame is None:
            continue
        
        frames += 1
        current_time = time.time()
        elapsed = current_time - prev_time

        # Calculate FPS every second
        if elapsed > 1.0:
            print(f"🚀 Threaded Software FPS: {frames / elapsed:.1f}")
            prev_time = current_time
            frames = 0

        display_frame = cv2.resize(frame, (960, 540))
        cv2.imshow("90 FPS Foosgoos Stream", display_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    stream.stop()
    cv2.destroyAllWindows()