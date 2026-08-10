"""
Turns 4 detected table-corner keypoints into a Homography matrix that
maps camera pixel coordinates -> normalized table coordinates (0..1
along each axis), per ARCHITECTURE.md Part 3 / Model 1.
"""
import time
import numpy as np
import cv2


class TableHomography:
    def __init__(self, refresh_interval_s: float = 15.0, corner_shift_thresh_px: float = 25.0):
        self._matrix = None
        self._last_computed = 0.0
        self._last_corners = None
        self.refresh_interval_s = refresh_interval_s
        self.corner_shift_thresh_px = corner_shift_thresh_px

    @property
    def is_calibrated(self) -> bool:
        return self._matrix is not None

    def needs_refresh(self) -> bool:
        if self._matrix is None:
            return True
        return (time.time() - self._last_computed) > self.refresh_interval_s

    def update(self, corners_px: dict) -> bool:
        """
        corners_px: {"top_left": (x,y), "top_right": (x,y),
                     "bottom_right": (x,y), "bottom_left": (x,y)}
        Returns True if the homography was (re)computed.
        """
        required = ("top_left", "top_right", "bottom_right", "bottom_left")
        if not all(k in corners_px for k in required):
            return False

        src = np.array([corners_px[k] for k in required], dtype=np.float32)
        dst = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32)

        if self._table_bumped(src):
            print("[homography] Corner positions shifted significantly - "
                  "recalibrating (table may have been bumped).")

        matrix = cv2.getPerspectiveTransform(src, dst)
        self._matrix = matrix
        self._last_corners = src
        self._last_computed = time.time()
        return True

    def _table_bumped(self, new_corners: np.ndarray) -> bool:
        if self._last_corners is None:
            return False
        shift = np.linalg.norm(new_corners - self._last_corners, axis=1)
        return bool(np.any(shift > self.corner_shift_thresh_px))

    def to_normalized(self, px: float, py: float):
        if self._matrix is None:
            raise RuntimeError("Homography not calibrated yet - run the "
                                "Architect model on a frame first.")
        pt = np.array([[[px, py]]], dtype=np.float32)
        out = cv2.perspectiveTransform(pt, self._matrix)
        nx, ny = out[0][0]
        return float(nx), float(ny)
