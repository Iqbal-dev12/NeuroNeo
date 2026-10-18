"""
services/face_detection.py
MediaPipe-based infant face detection with OpenCV fallback.

Pipeline
--------
raw image bytes → OpenCV frame → face detection → crop → return face ROI
"""

from typing import Optional

import cv2
import numpy as np
from loguru import logger

# ─── MediaPipe setup ─────────────────────────────────────────────────────────

# Try to import Mediapipe, but don't crash if it's missing (common on Python 3.13)
HAS_MEDIAPIPE = False
try:
    import mediapipe as mp
    try:
        import mediapipe.python.solutions.face_detection as mp_face_detection
    except ImportError:
        import mediapipe.solutions.face_detection as mp_face_detection
    _mp_face_detection = mp_face_detection
    HAS_MEDIAPIPE = True
except (ImportError, ModuleNotFoundError):
    logger.warning("MediaPipe not found or incompatible. Face detection will use OpenCV Haar Cascades.")
    _mp_face_detection = None


class FaceDetector:
    """
    Detects infant faces in images using MediaPipe Face Detection.

    Falls back to OpenCV Haar Cascade when MediaPipe finds nothing.
    """

    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        model_selection: int = 0,   # 0 = short-range (≤ 2 m), 1 = full-range
    ) -> None:
        if HAS_MEDIAPIPE and _mp_face_detection:
            self._detector = _mp_face_detection.FaceDetection(
                model_selection=model_selection,
                min_detection_confidence=min_detection_confidence,
            )
        else:
            self._detector = None

        # Haar cascade fallback
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self._cascade = cv2.CascadeClassifier(cascade_path)
        logger.info(
            "FaceDetector initialised (confidence={}, model_selection={})",
            min_detection_confidence,
            model_selection,
        )

    # ── Public API ──────────────────────────────────────────────────────────

    def detect_and_crop(
        self, image: np.ndarray, padding_ratio: float = 0.2
    ) -> Optional[np.ndarray]:
        """
        Detect the largest face and return a padded crop.

        Parameters
        ----------
        image : BGR OpenCV ndarray
        padding_ratio : extra margin around the detected bounding box (0–1)

        Returns
        -------
        Cropped BGR face region, or ``None`` if no face was found.
        """
        bbox = None
        if self._detector:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            result = self._detector.process(rgb)
            if result.detections:
                bbox = self._best_bbox(result.detections, image.shape)
                logger.debug("MediaPipe detected face: {}", bbox)
        
        if bbox is None:
            logger.debug("MediaPipe skipped or found no face; trying Haar cascade …")
            bbox = self._haar_fallback(image)

        if bbox is None:
            logger.warning("No face detected in the image.")
            return None

        return self._crop_with_padding(image, bbox, padding_ratio)

    def detect_and_draw(self, image: np.ndarray) -> np.ndarray:
        """
        Return a copy of *image* with the detected face box drawn on it.
        Useful for debugging streams.
        """
        annotated = image.copy()
        if self._detector:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            result = self._detector.process(rgb)
            if result.detections:
                for detection in result.detections:
                    bboxC = detection.location_data.relative_bounding_box
                    h, w = image.shape[:2]
                    x = int(bboxC.xmin * w)
                    y = int(bboxC.ymin * h)
                    bw = int(bboxC.width * w)
                    bh = int(bboxC.height * h)
                    cv2.rectangle(annotated, (x, y), (x + bw, y + bh), (0, 255, 0), 2)
        else:
            # Draw using haar if mediapipe is missing
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self._cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            for (x, y, w, h) in faces:
                cv2.rectangle(annotated, (x, y), (x + w, y + h), (255, 0, 0), 2)

        return annotated

    # ── Internals ────────────────────────────────────────────────────────────

    def _best_bbox(
        self, detections: list, shape: tuple
    ) -> dict[str, int]:
        """Pick the detection with the largest bounding-box area."""
        h, w = shape[:2]
        best = max(
            detections,
            key=lambda d: (
                d.location_data.relative_bounding_box.width
                * d.location_data.relative_bounding_box.height
            ),
        )
        bb = best.location_data.relative_bounding_box
        return {
            "x": int(bb.xmin * w),
            "y": int(bb.ymin * h),
            "w": int(bb.width * w),
            "h": int(bb.height * h),
        }

    def _haar_fallback(self, image: np.ndarray) -> Optional[dict[str, int]]:
        """Detect face using OpenCV Haar Cascade."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self._cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        if len(faces) == 0:
            return None
        # pick the largest
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        logger.debug("Haar cascade fallback detected face: x={} y={} w={} h={}", x, y, w, h)
        return {"x": int(x), "y": int(y), "w": int(w), "h": int(h)}

    def _crop_with_padding(
        self, image: np.ndarray, bbox: dict[str, int], ratio: float
    ) -> np.ndarray:
        """Return the face crop with proportional padding clamped to image bounds."""
        h, w = image.shape[:2]
        pad_x = int(bbox["w"] * ratio)
        pad_y = int(bbox["h"] * ratio)

        x1 = max(0, bbox["x"] - pad_x)
        y1 = max(0, bbox["y"] - pad_y)
        x2 = min(w, bbox["x"] + bbox["w"] + pad_x)
        y2 = min(h, bbox["y"] + bbox["h"] + pad_y)

        return image[y1:y2, x1:x2]

    def close(self) -> None:
        if self._detector:
            self._detector.close()


# ─── Module-level singleton ───────────────────────────────────────────────────

_face_detector: Optional[FaceDetector] = None


def get_face_detector() -> FaceDetector:
    """Return the module-level FaceDetector singleton (lazy-init)."""
    global _face_detector
    if _face_detector is None:
        _face_detector = FaceDetector()
    return _face_detector
