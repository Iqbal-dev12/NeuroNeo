"""
utils/image_utils.py
Image I/O helpers and centralised logging configuration (Loguru).
"""

import base64
import io
import os
import uuid
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from loguru import logger
from PIL import Image

# ─── Paths ───────────────────────────────────────────────────────────────────

# Resolve relative to the *project root* (two levels above this file)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
UPLOAD_DIR = _PROJECT_ROOT / "uploads"
DEMO_SAMPLES_DIR = _PROJECT_ROOT / "demo_samples"
LOG_DIR = _PROJECT_ROOT / "logs"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DEMO_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


# ─── Logging setup ────────────────────────────────────────────────────────────

def configure_logging() -> None:
    """
    Configure Loguru sinks:
    - Console (INFO+)
    - Rotating daily log file (DEBUG+)
    - Error-only log file (ERROR+)
    """
    logger.remove()  # remove default stderr handler

    # Console
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level="INFO",
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )

    # Daily rotating general log
    logger.add(
        sink=str(LOG_DIR / "app_{time:YYYY-MM-DD}.log"),
        level="DEBUG",
        rotation="00:00",       # new file every midnight
        retention="14 days",
        compression="zip",
        enqueue=True,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )

    # Error-only log
    logger.add(
        sink=str(LOG_DIR / "errors_{time:YYYY-MM-DD}.log"),
        level="ERROR",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        enqueue=True,
        format="{time} | {level} | {name}:{function}:{line} | {message}\n{exception}",
    )

    logger.info("Logging configured. Log directory: {}", LOG_DIR)


# ─── Image helpers ────────────────────────────────────────────────────────────

def save_uploaded_image(file_bytes: bytes, extension: str = "jpg") -> str:
    """
    Persist raw image bytes to the uploads folder.

    Returns the relative path string, e.g. ``uploads/abc123.jpg``.
    """
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{extension}"
    file_path = UPLOAD_DIR / filename
    file_path.write_bytes(file_bytes)
    logger.debug("Saved uploaded image → {}", file_path)
    return f"uploads/{filename}"


def bytes_to_cv2(image_bytes: bytes) -> np.ndarray:
    """Convert raw bytes → OpenCV BGR ndarray."""
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image bytes into an OpenCV frame.")
    return img


def cv2_to_bytes(img: np.ndarray, ext: str = ".jpg") -> bytes:
    """Convert an OpenCV BGR ndarray → JPEG/PNG bytes."""
    success, buf = cv2.imencode(ext, img)
    if not success:
        raise ValueError("cv2.imencode failed.")
    return buf.tobytes()


def base64_to_cv2(b64_string: str) -> np.ndarray:
    """Decode a base-64 string (with or without data-URI prefix) → OpenCV frame."""
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[1]
    raw = base64.b64decode(b64_string)
    return bytes_to_cv2(raw)


def cv2_to_base64(img: np.ndarray, ext: str = ".jpg") -> str:
    """Convert OpenCV frame → base-64 data-URI string."""
    raw = cv2_to_bytes(img, ext)
    encoded = base64.b64encode(raw).decode("utf-8")
    mime = "image/jpeg" if ext == ".jpg" else "image/png"
    return f"data:{mime};base64,{encoded}"


def resize_image(img: np.ndarray, size: tuple[int, int] = (224, 224)) -> np.ndarray:
    """Resize an OpenCV image to *size* (width, height)."""
    return cv2.resize(img, size, interpolation=cv2.INTER_AREA)


def preprocess_for_model(img: np.ndarray, size: tuple[int, int] = (224, 224)) -> np.ndarray:
    """
    Prepare an OpenCV BGR image for MobileNetV2 inference.

    Steps:
    1. Resize to *size*
    2. Convert BGR → RGB
    3. Normalise pixel values to [0, 1]
    4. Add batch dimension → shape (1, H, W, 3)
    """
    resized = cv2.resize(img, size, interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    normalised = rgb.astype(np.float32) / 255.0
    return np.expand_dims(normalised, axis=0)


def save_heatmap_image(heatmap_bgr: np.ndarray) -> str:
    """
    Save a heatmap image to the uploads directory.

    Returns the relative path string, e.g. ``uploads/heatmap_abc123.jpg``.
    """
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"heatmap_{uuid.uuid4().hex}.jpg"
    file_path = UPLOAD_DIR / filename
    cv2.imwrite(str(file_path), heatmap_bgr)
    logger.debug("Saved heatmap → {}", file_path)
    return f"uploads/{filename}"
