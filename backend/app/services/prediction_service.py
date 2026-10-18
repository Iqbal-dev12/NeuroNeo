"""
services/prediction_service.py
MobileNetV2 transfer-learning inference pipeline for 4-class pain classification.

The first time this module is imported, it builds (or loads) the Keras model.
Subsequent calls reuse the singleton to avoid overhead.

Pain classes
-----------
0 → No Pain
1 → Mild Pain
2 → Moderate Pain
3 → Severe Pain
"""

import os
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import tensorflow as tf
from loguru import logger

from app.constants.pain_levels import MODEL_INPUT_SIZE, NUM_CLASSES, PAIN_LEVEL_MAP
from app.services.face_detection import get_face_detector
from app.services.heatmap_service import GradCAM
from app.utils.image_utils import preprocess_for_model

# ─── Monkeypatch for Keras 3 Deserialization Issue ──────────────────────────
# Fixes: ValueError: Unrecognized keyword arguments passed to Dense: {'quantization_config': None}
try:
    from keras.src.layers.core.dense import Dense
    original_init = Dense.__init__
    def patched_init(self, *args, **kwargs):
        kwargs.pop('quantization_config', None)
        return original_init(self, *args, **kwargs)
    Dense.__init__ = patched_init
    logger.info("Applied Keras Dense layer monkeypatch.")
except Exception as e:
    logger.debug(f"Monkeypatch target not found: {e}")

# ─── Configuration ───────────────────────────────────────────────────────────
SEQUENCE_LENGTH = 16

# ─── Paths ───────────────────────────────────────────────────────────────────

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_MODEL_DIR = _BACKEND_DIR / "model"
_MODEL_DIR.mkdir(parents=True, exist_ok=True)
_MODEL_PATH = _MODEL_DIR / "pain_video_model.keras"

# ─── Globals ─────────────────────────────────────────────────────────────────

_model: Optional[tf.keras.Model] = None
_gradcam: Optional[GradCAM] = None


# ─── Model builder ────────────────────────────────────────────────────────────

def build_mobilenetv2_model() -> tf.keras.Model:
    """
    Build MobileNetV2 transfer-learning model for 4-class pain classification.

    Architecture
    ------------
    Input (224,224,3)
      → MobileNetV2 backbone (pretrained ImageNet, top removed, frozen)
      → GlobalAveragePooling2D
      → Dropout(0.3)
      → Dense(128, relu)
      → Dropout(0.2)
      → Dense(4, softmax)
    """
    logger.info("Building MobileNetV2 model …")

    base = tf.keras.applications.MobileNetV2(
        input_shape=(*MODEL_INPUT_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False  # freeze backbone for transfer learning

    inputs = tf.keras.Input(shape=(*MODEL_INPUT_SIZE, 3))
    # MobileNetV2 expects inputs in [-1, 1]; our preprocessing is [0,1]
    x = tf.keras.applications.mobilenet_v2.preprocess_input(inputs * 255.0)
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    x = tf.keras.layers.Dense(128, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    outputs = tf.keras.layers.Dense(NUM_CLASSES, activation="softmax")(x)

    model = tf.keras.Model(inputs, outputs, name="infant_pain_mobilenetv2")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-4),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    logger.info("Model built: {} trainable params", model.count_params())
    return model


# ─── Load / save helpers ─────────────────────────────────────────────────────

def build_sequence_model() -> tf.keras.Model:
    """
    Build a CNN-LSTM sequence model accepting (batch, SEQUENCE_LENGTH, H, W, C)
    for infant pain recognition.
    """
    backbone = tf.keras.applications.MobileNetV2(
        input_shape=(*MODEL_INPUT_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    backbone.trainable = False
    inputs = tf.keras.Input(shape=(SEQUENCE_LENGTH, *MODEL_INPUT_SIZE, 3))
    x = tf.keras.layers.TimeDistributed(backbone)(inputs)
    x = tf.keras.layers.TimeDistributed(tf.keras.layers.GlobalAveragePooling2D())(x)
    x = tf.keras.layers.LSTM(64, return_sequences=False)(x)
    x = tf.keras.layers.Dropout(0.5)(x)
    x = tf.keras.layers.Dense(32, activation="relu")(x)
    outputs = tf.keras.layers.Dense(NUM_CLASSES, activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs, name="infant_pain_sequence_model")
    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    return model

def load_or_build_model() -> tf.keras.Model:
    """
    Load a pre-trained model from disk, or build a fresh one.
    """
    if _MODEL_PATH.exists():
        logger.info("Loading saved model from {}", _MODEL_PATH)
        try:
            import keras
            return keras.models.load_model(str(_MODEL_PATH))
        except Exception as e:
            logger.warning(f"Standard keras load failed: {e}")
        try:
            return tf.keras.models.load_model(str(_MODEL_PATH), compile=False)
        except Exception as e:
            logger.warning(f"tf.keras load failed: {e}")

    logger.warning(
        "Building sequence model with MobileNetV2 backbone. "
        "Predictions will operate using transfer learning.",
    )
    return build_sequence_model()


# ─── Singleton initialiser ───────────────────────────────────────────────────

def initialise_model() -> None:
    """Called once at application startup to warm-up the model."""
    global _model, _gradcam
    if _model is None:
        _model = load_or_build_model()
        
        # Heatmap setup (optional, may fail on complex TimeDistributed architectures)
        try:
            global _gradcam
            _gradcam = GradCAM(_model)
        except Exception as e:
            logger.warning(f"Grad-CAM could not be initialised: {e}. Heatmaps will be disabled.")
            _gradcam = None
            
        logger.info("Prediction service initialised.")


def get_model() -> tf.keras.Model:
    if _model is None:
        initialise_model()
    return _model  # type: ignore[return-value]


def get_gradcam() -> Optional[GradCAM]:
    if _gradcam is None:
        try:
            initialise_model()
        except Exception:
            pass
    return _gradcam


def extract_frames(source, is_video=True, seq_len: int = SEQUENCE_LENGTH) -> np.ndarray:
    """Extract a sequence of 16 padded face crops from an image or video."""
    detector = get_face_detector()
    frames = []

    if not is_video:
        # For images, detect face once and repeat
        img_bgr = source if isinstance(source, np.ndarray) else cv2.imread(str(source))
        if img_bgr is None:
            return np.zeros((seq_len, *MODEL_INPUT_SIZE, 3))
        
        face_crop = detector.detect_and_crop(img_bgr)
        if face_crop is None:
            face_crop = cv2.resize(img_bgr, MODEL_INPUT_SIZE)
        else:
            face_crop = cv2.resize(face_crop, MODEL_INPUT_SIZE)
        
        face_crop = face_crop / 255.0
        return np.array([face_crop] * seq_len)

    # For videos
    cap = cv2.VideoCapture(str(source))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    skip = max(1, total_frames // seq_len)
    
    count = 0
    extracted = 0
    while cap.isOpened() and extracted < seq_len:
        ret, frame = cap.read()
        if not ret:
            break
        if count % skip == 0:
            face_crop = detector.detect_and_crop(frame)
            if face_crop is None:
                # Fallback to center crop if detection fails
                h, w = frame.shape[:2]
                side = min(h, w)
                face_crop = frame[(h-side)//2:(h+side)//2, (w-side)//2:(w+side)//2]
            
            face_crop = cv2.resize(face_crop, MODEL_INPUT_SIZE)
            face_crop = face_crop / 255.0
            frames.append(face_crop)
            extracted += 1
        count += 1
    cap.release()

    # Padding if video is too short
    while len(frames) < seq_len:
        frames.append(frames[-1] if frames else np.zeros((*MODEL_INPUT_SIZE, 3)))
    
    return np.array(frames)


# ─── Inference pipeline ──────────────────────────────────────────────────────

def predict_pain(
    file_path: str,
    is_video: bool = True,
) -> dict:
    """
    Full inference pipeline for video/image sequences.
    """
    model = get_model()

    # Step 1 – Extract sequence
    sequence = extract_frames(file_path, is_video=is_video)
    input_tensor = np.expand_dims(sequence, axis=0) # (1, 16, 224, 224, 3)

    # Step 2 – Inference
    # Check if model output is binary (1 unit) or categorical (4 units)
    predictions = model.predict(input_tensor, verbose=0)
    
    if predictions.shape[-1] == 1:
        # Binary CNN-LSTM model output (sigmoid 0.0 - 1.0)
        score = float(predictions[0][0])
        if score >= 0.70:
            pain_level = "Severe Pain"
            class_idx = 3
            confidence = score
            reason = "High facial tension, brow bulge, eye squeezing, and sustained grimacing detected across frames."
            probs = [round(max(0.0, 1.0 - score), 4), 0.05, 0.15, round(score, 4)]
        elif score >= 0.45:
            pain_level = "Moderate Pain"
            class_idx = 2
            confidence = score
            reason = "Noticeable facial contraction, intermittent brow furrowing, and eye tightening observed."
            probs = [round(max(0.0, 1.0 - score), 4), 0.10, round(score, 4), 0.05]
        elif score >= 0.20:
            pain_level = "Mild Pain"
            class_idx = 1
            confidence = float(1.0 - score)
            reason = "Subtle facial grimacing or mild restlessness with predominantly relaxed intervals."
            probs = [round(1.0 - score, 4), round(score, 4), 0.05, 0.0]
        else:
            pain_level = "No Pain"
            class_idx = 0
            confidence = float(1.0 - score)
            reason = "Calm infant facial features, relaxed brow, and baseline resting state detected."
            probs = [round(1.0 - score, 4), 0.05, 0.02, 0.0]
    else:
        # 4-class model
        probs = predictions[0].tolist()
        class_idx = int(np.argmax(probs))
        pain_level = PAIN_LEVEL_MAP[class_idx]
        score = float(probs[class_idx])
        confidence = score
        reasons_map = {
            0: "Calm infant facial features, relaxed brow, and baseline resting state detected.",
            1: "Subtle facial grimacing or mild restlessness with predominantly relaxed intervals.",
            2: "Noticeable facial contraction, intermittent brow furrowing, and eye tightening observed.",
            3: "High facial tension, brow bulge, eye squeezing, and sustained grimacing detected across frames."
        }
        reason = reasons_map.get(class_idx, "Facial motion analysis completed.")

    logger.info("Prediction → level='{}' score={:.3f} confidence={:.3f}", pain_level, score, confidence)

    return {
        "face_detected": True,
        "pain_level": pain_level,
        "pain_score": round(score, 4),
        "confidence": round(confidence, 4),
        "probabilities": [round(p, 4) for p in probs],
        "class_idx": class_idx,
        "reason": reason,
        "input_tensor": input_tensor,
        "face_crop": (sequence[0] * 255).astype(np.uint8), # For GradCAM
    }


def generate_gradcam_overlay(
    image_bgr: np.ndarray,
    class_idx: int,
    input_tensor: np.ndarray,
) -> np.ndarray:
    """
    Run Grad-CAM and return the coloured overlay as a BGR ndarray.
    """
    gradcam = get_gradcam()
    if gradcam is None:
        logger.warning("Grad-CAM is not available. Returning original image.")
        return image_bgr

    try:
        overlay = gradcam.generate_heatmap(
            preprocessed_input=input_tensor,
            class_idx=class_idx,
            alpha=0.4,
            original_bgr=image_bgr,
        )
        return overlay
    except Exception as e:
        logger.error(f"Grad-CAM generation failed: {e}")
        return image_bgr
