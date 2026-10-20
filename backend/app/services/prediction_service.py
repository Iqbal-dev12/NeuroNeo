
"""
services/prediction_service.py

Memory-conscious inference pipeline for the MobileNetV2 CNN-LSTM
infant pain classification model.

Pain classes:
0 -> No Pain
1 -> Mild Pain
2 -> Moderate Pain
3 -> Severe Pain
"""

import os

# Set thread limits before TensorFlow initializes its runtime.
os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "1")
os.environ.setdefault("TF_NUM_INTEROP_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

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
MAX_DETECTION_FRAME_SIDE = 640

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_MODEL_DIR = _BACKEND_DIR / "model"
_MODEL_DIR.mkdir(parents=True, exist_ok=True)
_MODEL_PATH = _MODEL_DIR / "pain_video_model.keras"

_model: Optional[tf.keras.Model] = None
_gradcam: Optional[GradCAM] = None


# ─── Model builders ───────────────────────────────────────────────────────

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
    """Build the CNN-LSTM model for a sequence of video frames."""

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
    """Load the saved model, or build a fallback sequence model."""

    if _MODEL_PATH.exists():
        logger.info("Loading saved model from {}", _MODEL_PATH)

        try:
            import keras

            return keras.models.load_model(str(_MODEL_PATH))

        except Exception as exc:
            logger.warning("Standard Keras model loading failed: {}", exc)

        try:
            return tf.keras.models.load_model(
                str(_MODEL_PATH),
                compile=False,
            )

        except Exception as exc:
            logger.warning("TensorFlow model loading failed: {}", exc)

    logger.warning(
        "No compatible saved model was loaded. "
        "Building a new sequence model; this is not a trained "
        "replacement for your saved model."
    )

    return build_sequence_model()


def initialise_model() -> None:
    """Initialize the model once and set up optional Grad-CAM."""

    global _model, _gradcam

    if _model is not None:
        return

    _model = load_or_build_model()

    try:
        _gradcam = GradCAM(_model)
        logger.info("Grad-CAM initialized.")

    except Exception as exc:
        _gradcam = None
        logger.warning(
            "Grad-CAM initialization failed; heatmaps are disabled: {}",
            exc,
        )

    logger.info(
        "Prediction service initialized. Model output units: {}",
        _model.output_shape[-1],
    )


def get_model() -> tf.keras.Model:
    """Return the initialized model."""

    if _model is None:
        initialise_model()

    if _model is None:
        raise RuntimeError("The prediction model could not be initialized.")

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
    Extract a fixed-length sequence of normalized RGB-order-compatible
    image arrays from a video or image.

    OpenCV returns BGR frames. This preserves the original pipeline's
    channel ordering; it does not introduce an RGB conversion.
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

    # Direct inference avoids the model.predict data-adapter overhead.
    predictions_tensor = model(input_tensor, training=False)
    predictions = predictions_tensor.numpy()

    del predictions_tensor

    if predictions.ndim != 2 or predictions.shape[0] != 1:
        raise ValueError(
            f"Unexpected model output shape: {predictions.shape}"
        )

    output_units = predictions.shape[-1]

    if output_units == 1:
        # Preserve the original binary-score interpretation.
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
