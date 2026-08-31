"""
Turns 4 table-corner points into a homography that maps camera pixels ->
normalized table coordinates (0..1 on each axis).

x runs along the LENGTH of the table: 0.0 is the blue goal, 1.0 is the
red goal. y runs across the width. Every downstream number - goal lines,
rod positions, speed limits - is in these units, so they stay valid even
though the table drifts a few centimetres a day.
"""
import json
import time
from pathlib import Path

import numpy as np
import cv2

import config

CORNER_ORDER = ("top_left", "top_right", "bottom_right", "bottom_left")


class TableHomography:
    def __init__(self, refresh_interval_s=None, bump_threshold_px=None):
        self._matrix = None
        self._last_computed = 0.0
        self._last_corners = None
        self._source = None
        self.refresh_interval_s = (
            config.ARCHITECT_REFRESH_INTERVAL_S if refresh_interval_s is None
            else refresh_interval_s
        )
        self.bump_threshold_px = (
            config.ARCHITECT_BUMP_THRESHOLD_PX if bump_threshold_px is None
            else bump_threshold_px
        )
        self.bump_count = 0

    # -- state -----------------------------------------------------

    @property
    def is_calibrated(self) -> bool:
        return self._matrix is not None

    @property
    def source(self):
        return self._source

    @property
    def corners(self):
        if self._last_corners is None:
            return None
        return {k: tuple(map(float, xy))
                for k, xy in zip(CORNER_ORDER, self._last_corners)}

    def needs_refresh(self) -> bool:
        if self._matrix is None:
            return True
        return (time.time() - self._last_computed) > self.refresh_interval_s

    def age_s(self) -> float:
        return time.time() - self._last_computed

    # -- updating --------------------------------------------------

    def update(self, corners_px: dict, source: str = "architect") -> bool:
        """(Re)compute the matrix from four corner points.

        corners_px maps each name in CORNER_ORDER to an (x, y) pixel pair.
        Returns True if the matrix was recomputed.
        """
        if not all(k in corners_px for k in CORNER_ORDER):
            return False

        src = np.array([corners_px[k] for k in CORNER_ORDER], dtype=np.float32)
        if not _is_sane_quad(src):
            # A collapsed or self-intersecting quad means the keypoint
            # model produced garbage this frame. Keeping the previous
            # good matrix beats scrambling every coordinate downstream.
            return False

        if self._table_bumped(src):
            self.bump_count += 1
            print(f"[homography] table moved (>{self.bump_threshold_px:.0f}px) "
                  f"- recalibrating, bump #{self.bump_count}")

        dst = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32)
        self._matrix = cv2.getPerspectiveTransform(src, dst)
        self._last_corners = src
        self._last_computed = time.time()
        self._source = source
        return True

    def _table_bumped(self, new_corners: np.ndarray) -> bool:
        if self._last_corners is None:
            return False
        shift = np.linalg.norm(new_corners - self._last_corners, axis=1)
        return bool(np.any(shift > self.bump_threshold_px))

    # -- use -------------------------------------------------------

    def to_normalized(self, px: float, py: float):
        if self._matrix is None:
            raise RuntimeError(
                "Homography not calibrated. Either train the Architect model "
                "or run `python -m tools.calibrate_corners` first."
            )
        pt = np.array([[[px, py]]], dtype=np.float32)
        nx, ny = cv2.perspectiveTransform(pt, self._matrix)[0][0]
        return float(nx), float(ny)

    def to_pixels(self, nx: float, ny: float):
        """Inverse: normalized table coords -> camera pixels. Used to draw
        goal lines and rod positions on the debug overlay."""
        if self._matrix is None:
            raise RuntimeError("Homography not calibrated")
        inv = np.linalg.inv(self._matrix)
        pt = np.array([[[nx, ny]]], dtype=np.float32)
        px, py = cv2.perspectiveTransform(pt, inv)[0][0]
        return float(px), float(py)

    # -- persistence -----------------------------------------------

    def save(self, path=None):
        path = Path(path or config.CALIBRATION_PATH)
        payload = {
            "corners": self.corners,
            "source": self._source,
            "saved_at": time.time(),
            "crop": [config.CROP_Y1, config.CROP_Y2, config.CROP_X1, config.CROP_X2],
        }
        path.write_text(json.dumps(payload, indent=2))
        return path

    def load(self, path=None) -> bool:
        path = Path(path or config.CALIBRATION_PATH)
        if not path.exists():
            return False
        data = json.loads(path.read_text())
        corners = data.get("corners") or {}
        saved_crop = data.get("crop")
        current_crop = [config.CROP_Y1, config.CROP_Y2, config.CROP_X1, config.CROP_X2]
        if saved_crop and saved_crop != current_crop:
            print(f"[homography] WARNING: {path.name} was saved with crop "
                  f"{saved_crop} but config now says {current_crop}. The saved "
                  f"corners refer to a differently framed image - recalibrate.")
        return self.update({k: tuple(v) for k, v in corners.items()},
                           source=f"file:{path.name}")


def _is_sane_quad(pts: np.ndarray) -> bool:
    """Reject degenerate corner sets before they poison the matrix."""
    if pts.shape != (4, 2):
        return False
    if not np.isfinite(pts).all():
        return False
    # Every corner must be distinct by a real margin.
    for i in range(4):
        for j in range(i + 1, 4):
            if np.linalg.norm(pts[i] - pts[j]) < 10:
                return False
    # Shoelace area - a valid quad in tl,tr,br,bl order encloses real area.
    x, y = pts[:, 0], pts[:, 1]
    area = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
    return area > 1000.0
