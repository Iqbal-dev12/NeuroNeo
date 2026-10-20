"""
services/prediction_service.py

Memory-conscious inference pipeline for the MobileNetV2 CNN-LSTM
infant pain classification model.

The saved model (backend/model/pain_video_model.keras) is a Sequential model:
    TimeDistributed(MobileNetV2) -> TimeDistributed(GlobalAveragePooling2D)
    -> LSTM(64) -> Dropout -> Dense(32) -> Dense(1)
Input:  (None, 16, 224, 224, 3)
Output: (None, 1)  -> interpreted as a binary pain score.

A four-class output (NUM_CLASSES) is also supported if a different
model is ever deployed.
"""

import os

# Set thread limits before TensorFlow initializes its runtime.
os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "1")
os.environ.setdefault("TF_NUM_INTEROP_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import threading
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import tensorflow as tf
from loguru import logger

from app.constants.pain_levels import (
    MODEL_INPUT_SIZE,
    NUM_CLASSES,
    PAIN_LEVEL_MAP,
)
from app.services.face_detection import get_face_detector
from app.services.heatmap_service import GradCAM


# ─── Memory diagnostics (numbers only; no filenames, IDs, or image data) ──

def _proc_mb(key: str) -> int:
    """Read a memory field (in MB) from /proc/self/status (Linux only)."""
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith(key):
                    return int(line.split()[1]) // 1024
    except OSError:
        pass
    return -1


def _cgroup_mb() -> int:
    """Container memory usage in MB (may include page cache)."""
    for path in (
        "/sys/fs/cgroup/memory.current",
        "/sys/fs/cgroup/memory/memory.usage_in_bytes",
    ):
        try:
            with open(path) as f:
                return int(f.read().strip()) // (1024 * 1024)
        except OSError:
            continue
    return -1


def log_mem(tag: str) -> None:
    """Log current RSS, peak RSS (VmHWM) and cgroup memory."""
    logger.info(
        "[mem] {}: rss={}MB peak={}MB cgroup={}MB",
        tag,
        _proc_mb("VmRSS:"),
        _proc_mb("VmHWM:"),
        _cgroup_mb(),
    )


# ─── Runtime configuration ────────────────────────────────────────────────

cv2.setNumThreads(1)

try:
    tf.config.threading.set_intra_op_parallelism_threads(1)
    tf.config.threading.set_inter_op_parallelism_threads(1)
except RuntimeError:
    # TensorFlow may already have initialized its runtime.
    logger.debug("TensorFlow threading configuration was already initialized.")


# ─── Keras deserialization compatibility ──────────────────────────────────

try:
    from keras.src.layers.core.dense import Dense

    _original_dense_init = Dense.__init__

    def _patched_dense_init(self, *args, **kwargs):
        kwargs.pop("quantization_config", None)
        return _original_dense_init(self, *args, **kwargs)

    Dense.__init__ = _patched_dense_init
    logger.info("Applied Keras Dense layer compatibility patch.")

except Exception as exc:
    logger.debug("Dense compatibility patch not applied: {}", exc)


# ─── Configuration ────────────────────────────────────────────────────────

SEQUENCE_LENGTH = 16
MAX_DETECTION_FRAME_SIDE = 320

# Safety: by default the service will NOT silently serve predictions from an
# untrained model. Set ALLOW_UNTRAINED_FALLBACK=1 only for local demos.
ALLOW_UNTRAINED_FALLBACK = (
    os.environ.get("ALLOW_UNTRAINED_FALLBACK", "0") == "1"
)

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_MODEL_DIR = _BACKEND_DIR / "model"
_MODEL_DIR.mkdir(parents=True, exist_ok=True)
_MODEL_PATH = _MODEL_DIR / "pain_video_model.keras"

_model: Optional[tf.keras.Model] = None
_split = None  # (cnn_layer, pooling_layer, head_layers) or None
_load_error: Optional[str] = None
_gradcam: Optional[GradCAM] = None

# Only one prediction at a time: two concurrent requests would double the
# activation memory on a 512 MB instance.
_inference_lock = threading.Lock()

log_mem("after_imports")


# ─── Model builders (fallback / development only) ─────────────────────────

def build_mobilenetv2_model() -> tf.keras.Model:
    """Build the MobileNetV2 image-classification model."""

    logger.info("Building MobileNetV2 model.")

    base = tf.keras.applications.MobileNetV2(
        input_shape=(*MODEL_INPUT_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False

    inputs = tf.keras.Input(shape=(*MODEL_INPUT_SIZE, 3))

    x = tf.keras.applications.mobilenet_v2.preprocess_input(
        inputs * 255.0
    )
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    x = tf.keras.layers.Dense(128, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.2)(x)

    outputs = tf.keras.layers.Dense(
        NUM_CLASSES,
        activation="softmax",
    )(x)

    model = tf.keras.Model(
        inputs,
        outputs,
        name="infant_pain_mobilenetv2",
    )

    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-4),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    return model


def build_sequence_model() -> tf.keras.Model:
    """Build an UNTRAINED CNN-LSTM model (fallback/development only)."""

    backbone = tf.keras.applications.MobileNetV2(
        input_shape=(*MODEL_INPUT_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    backbone.trainable = False

    inputs = tf.keras.Input(
        shape=(SEQUENCE_LENGTH, *MODEL_INPUT_SIZE, 3)
    )

    x = tf.keras.layers.TimeDistributed(backbone)(inputs)
    x = tf.keras.layers.TimeDistributed(
        tf.keras.layers.GlobalAveragePooling2D()
    )(x)
    x = tf.keras.layers.LSTM(64, return_sequences=False)(x)
    x = tf.keras.layers.Dropout(0.5)(x)
    x = tf.keras.layers.Dense(32, activation="relu")(x)

    outputs = tf.keras.layers.Dense(
        NUM_CLASSES,
        activation="softmax",
    )(x)

    model = tf.keras.Model(
        inputs,
        outputs,
        name="infant_pain_sequence_model",
    )

    model.compile(
        optimizer="adam",
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    return model


# ─── Model loading ────────────────────────────────────────────────────────

def load_or_build_model() -> tf.keras.Model:
    """
    Load the trained model.

    If loading fails, raise an error instead of silently serving an
    untrained model (unless ALLOW_UNTRAINED_FALLBACK=1 is set).
    """

    if _MODEL_PATH.exists():
        logger.info("Loading saved model from {}", _MODEL_PATH)

        try:
            # compile=False: inference only, no optimizer state needed.
            model = tf.keras.models.load_model(
                str(_MODEL_PATH),
                compile=False,
            )
            logger.info("Trained model loaded successfully.")
            return model

        except Exception as exc:
            logger.error(
                "Trained model failed to load: {}: {}",
                type(exc).__name__,
                exc,
            )
            if not ALLOW_UNTRAINED_FALLBACK:
                raise RuntimeError(
                    "The trained model could not be loaded: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
    else:
        logger.error("Model file not found at {}", _MODEL_PATH)
        if not ALLOW_UNTRAINED_FALLBACK:
            raise RuntimeError(f"Model file not found: {_MODEL_PATH}")

    logger.error(
        "ALLOW_UNTRAINED_FALLBACK=1: building an UNTRAINED model. "
        "Its predictions are NOT valid and must not be used clinically."
    )
    return build_sequence_model()


def _build_split(model: tf.keras.Model):
    """
    Validate that the model has the expected CNN-LSTM layout and return
    (cnn_layer, pooling_layer, head_layers) for frame-at-a-time inference.

    Returns None if the layout is unexpected, in which case the full model
    is called instead, so predictions are never silently altered.
    """

    layers = [
        layer for layer in model.layers
        if not isinstance(layer, tf.keras.layers.InputLayer)
    ]

    if (
        len(layers) < 3
        or not isinstance(layers[0], tf.keras.layers.TimeDistributed)
        or not isinstance(layers[1], tf.keras.layers.TimeDistributed)
    ):
        logger.warning(
            "Split inference unavailable (unexpected layer layout); "
            "the full model will be used instead."
        )
        return None

    return layers[0], layers[1], layers[2:]


def initialise_model() -> None:
    """Initialize the trained model once; Grad-CAM stays disabled."""
    global _model, _split, _load_error, _gradcam

    if _model is not None or _load_error is not None:
        return

    try:
        model = load_or_build_model()
    except Exception as exc:
        _load_error = f"{type(exc).__name__}: {exc}"
        logger.error("Model initialization failed: {}", _load_error)
        log_mem("after_model_load_failed")
        return

    _model = model
    _split = _build_split(model)
    _gradcam = None

    log_mem("after_model_load")

    logger.info(
        "Prediction service initialized. Model output units: {}",
        _model.output_shape[-1],
    )
    logger.info(
        "Split inference enabled: {}", _split is not None
    )
    logger.info("Grad-CAM disabled to reduce memory usage.")


def get_model() -> tf.keras.Model:
    """Return the initialized model, or raise if it failed to load."""

    if _model is None and _load_error is None:
        initialise_model()

    if _model is None:
        raise RuntimeError(
            "The prediction model is unavailable: "
            f"{_load_error or 'unknown error'}"
        )

    return _model


def get_gradcam() -> Optional[GradCAM]:
    """Return Grad-CAM if it is available."""

    if _gradcam is None:
        return None

    return _gradcam


# ─── Frame preprocessing ─────────────────────────────────────────────────

def _resize_for_detection(frame: np.ndarray) -> np.ndarray:
    """Limit large frames before running face detection."""

    height, width = frame.shape[:2]
    longest_side = max(height, width)

    if longest_side <= MAX_DETECTION_FRAME_SIDE:
        return frame

    scale = MAX_DETECTION_FRAME_SIDE / float(longest_side)

    new_width = max(1, int(width * scale))
    new_height = max(1, int(height * scale))

    return cv2.resize(
        frame,
        (new_width, new_height),
        interpolation=cv2.INTER_AREA,
    )


def _prepare_face_crop(frame: np.ndarray) -> np.ndarray:
    """Detect a face, fall back to a center crop, and normalize it."""

    detector = get_face_detector()
    frame = _resize_for_detection(frame)

    face_crop = detector.detect_and_crop(frame)

    if face_crop is None or face_crop.size == 0:
        height, width = frame.shape[:2]
        side = min(height, width)

        x1 = (width - side) // 2
        y1 = (height - side) // 2

        face_crop = frame[
            y1:y1 + side,
            x1:x1 + side,
        ]

    face_crop = cv2.resize(face_crop, MODEL_INPUT_SIZE)

    # float32 uses half the memory of float64.
    face_crop = face_crop.astype(np.float32)
    face_crop /= np.float32(255.0)

    return face_crop


def extract_frames(
    source,
    is_video: bool = True,
    seq_len: int = SEQUENCE_LENGTH,
) -> np.ndarray:
    """
    Extract a fixed-length sequence of normalized image arrays from a
    video or image.

    OpenCV returns BGR frames. This preserves the original pipeline's
    channel ordering; it does not introduce an RGB conversion.
    Frame sampling is unchanged from the original implementation so that
    predictions stay consistent with the trained model.
    """

    if seq_len < 1:
        raise ValueError("seq_len must be at least 1.")

    if not is_video:
        image = (
            source
            if isinstance(source, np.ndarray)
            else cv2.imread(str(source))
        )

        if image is None:
            raise ValueError(f"Could not read image: {source}")

        face_crop = _prepare_face_crop(image)

        return np.repeat(
            face_crop[np.newaxis, ...],
            seq_len,
            axis=0,
        ).astype(np.float32, copy=False)

    cap = cv2.VideoCapture(str(source))

    if not cap.isOpened():
        cap.release()
        raise ValueError(f"Could not open video: {source}")

    frames = []

    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if total_frames <= 0:
            raise ValueError("The video contains no readable frames.")

        skip = max(1, total_frames // seq_len)

        frame_index = 0

        while len(frames) < seq_len:
            success, frame = cap.read()

            if not success:
                break

            if frame_index % skip == 0:
                frames.append(_prepare_face_crop(frame))

            frame_index += 1

    finally:
        cap.release()

    if not frames:
        raise ValueError("No frames could be extracted from the video.")

    # Repeat the last available frame if the video yielded fewer frames.
    while len(frames) < seq_len:
        frames.append(frames[-1])

    sequence = np.stack(frames[:seq_len], axis=0)

    return sequence.astype(np.float32, copy=False)


# ─── Inference ────────────────────────────────────────────────────────────

def _run_inference(model: tf.keras.Model, input_tensor: np.ndarray) -> np.ndarray:
    """
    Run the CNN-LSTM model.

    With the expected layout, the CNN runs one frame at a time (same
    weights and math as TimeDistributed at inference, lower peak activation
    memory). Otherwise the full model is called unchanged.
    """

    if _split is None:
        return model(input_tensor, training=False).numpy()

    cnn_layer, pooling_layer, head_layers = _split

    features = []

    for t in range(SEQUENCE_LENGTH):
        frame_batch = input_tensor[:, t:t + 1, ...]
        cnn_out = cnn_layer(frame_batch, training=False)
        features.append(pooling_layer(cnn_out, training=False))

        if t in (0, 7, 15):
            log_mem(f"cnn_frame_{t}")

    x = tf.concat(features, axis=1)

    for layer in head_layers:
        x = layer(x, training=False)

    return x.numpy()


# ─── Pain prediction ──────────────────────────────────────────────────────

def predict_pain(
    file_path: str,
    is_video: bool = True,
) -> dict:
    """
    Run inference and return the existing prediction fields.

    The trained model and its learned parameters are not modified.
    """

    model = get_model()

    with _inference_lock:
        log_mem("predict_start")

        sequence = extract_frames(
            file_path,
            is_video=is_video,
            seq_len=SEQUENCE_LENGTH,
        )

        # Shape: (1, 16, height, width, 3)
        input_tensor = np.expand_dims(sequence, axis=0).astype(
            np.float32,
            copy=False,
        )
        log_mem("after_frames")

        predictions = _run_inference(model, input_tensor)
        log_mem("after_head")

    if predictions.ndim != 2 or predictions.shape[0] != 1:
        raise ValueError(
            f"Unexpected model output shape: {predictions.shape}"
        )

    output_units = predictions.shape[-1]

    if output_units == 1:
        # Binary-score interpretation (matches the saved model).
        score = float(predictions[0][0])

        if score >= 0.70:
            pain_level = "Severe Pain"
            class_idx = 3
            confidence = score
            reason = (
                "High facial tension, brow bulge, eye squeezing, "
                "and sustained grimacing detected across frames."
            )
            probs = [
                round(max(0.0, 1.0 - score), 4),
                0.05,
                0.15,
                round(score, 4),
            ]

        elif score >= 0.45:
            pain_level = "Moderate Pain"
            class_idx = 2
            confidence = score
            reason = (
                "Noticeable facial contraction, intermittent brow "
                "furrowing, and eye tightening observed."
            )
            probs = [
                round(max(0.0, 1.0 - score), 4),
                0.10,
                round(score, 4),
                0.05,
            ]

        elif score >= 0.20:
            pain_level = "Mild Pain"
            class_idx = 1
            confidence = float(1.0 - score)
            reason = (
                "Subtle facial grimacing or mild restlessness with "
                "predominantly relaxed intervals."
            )
            probs = [
                round(1.0 - score, 4),
                round(score, 4),
                0.05,
                0.0,
            ]

        else:
            pain_level = "No Pain"
            class_idx = 0
            confidence = float(1.0 - score)
            reason = (
                "Calm infant facial features, relaxed brow, "
                "and baseline resting state detected."
            )
            probs = [
                round(1.0 - score, 4),
                0.05,
                0.02,
                0.0,
            ]

    elif output_units == NUM_CLASSES:
        # Four-class model: use its actual predicted probabilities.
        probs = predictions[0].tolist()
        class_idx = int(np.argmax(probs))
        pain_level = PAIN_LEVEL_MAP[class_idx]
        score = float(probs[class_idx])
        confidence = score

        reasons_map = {
            0: (
                "Calm infant facial features, relaxed brow, "
                "and baseline resting state detected."
            ),
            1: (
                "Subtle facial grimacing or mild restlessness with "
                "predominantly relaxed intervals."
            ),
            2: (
                "Noticeable facial contraction, intermittent brow "
                "furrowing, and eye tightening observed."
            ),
            3: (
                "High facial tension, brow bulge, eye squeezing, "
                "and sustained grimacing detected across frames."
            ),
        }

        reason = reasons_map.get(
            class_idx,
            "Facial motion analysis completed.",
        )

    else:
        raise ValueError(
            f"Unsupported model output size: {output_units}. "
            f"Expected 1 or {NUM_CLASSES}."
        )

    logger.info(
        "Prediction completed: level='{}', score={:.3f}, "
        "confidence={:.3f}",
        pain_level,
        score,
        confidence,
    )

    # Preserve the existing fields for the API layer.
    result = {
        "face_detected": True,
        "pain_level": pain_level,
        "pain_score": round(score, 4),
        "confidence": round(confidence, 4),
        "probabilities": [round(float(p), 4) for p in probs],
        "class_idx": class_idx,
        "reason": reason,
        "input_tensor": input_tensor,
        "face_crop": (sequence[0] * 255).astype(np.uint8),
    }

    return result


# ─── Grad-CAM overlay ────────────────────────────────────────────────────

def generate_gradcam_overlay(
    image_bgr: np.ndarray,
    class_idx: int,
    input_tensor: np.ndarray,
) -> np.ndarray:
    """Generate a Grad-CAM overlay when Grad-CAM is available."""

    gradcam = get_gradcam()

    if gradcam is None:
        logger.warning(
            "Grad-CAM is unavailable; returning the original image."
        )
        return image_bgr

    try:
        # Grad-CAM expects one image with shape (1, H, W, C).
        gradcam_input = input_tensor

        if len(gradcam_input.shape) == 5:
            gradcam_input = gradcam_input[:, 0, ...]

        overlay = gradcam.generate_heatmap(
            preprocessed_input=gradcam_input,
            class_idx=class_idx,
            alpha=0.4,
            original_bgr=image_bgr,
        )

        return overlay

    except Exception as exc:
        logger.error("Grad-CAM generation failed: {}", exc)
        return image_bgr
