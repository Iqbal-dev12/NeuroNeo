"""
inference_video.py
Run inference on a single video using the trained CNN-LSTM model.
"""

import os
import cv2
import numpy as np
import keras
import tensorflow as tf
from loguru import logger
import mediapipe as mp
import sys
from datetime import datetime
from pathlib import Path

# Add the backend directory to sys.path so we can import 'app'
# Assuming the script is run from backend/ directory
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.database.db import SessionLocal
from app.database import models
from app.constants.pain_levels import PAIN_LEVEL_MAP

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
    logger.debug(f"Monkeypatch target not found (might be using different Keras structure): {e}")

# ─── Configuration ───────────────────────────────────────────────────────────
#
# Resolve model path relative to the project, so it works for any user account.
_BACKEND_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _BACKEND_DIR.parents[1]  # ETHICARE HACKATHON/
MODEL_PATH = _PROJECT_ROOT / "hackathon" / "backend" / "model" / "pain_video_model.keras"
IMG_SIZE = 224
SEQUENCE_LENGTH = 16

# MediaPipe for face detection (with fallback to Haar Cascades)
HAS_MEDIAPIPE = False
try:
    import mediapipe as mp
    mp_face_detection = mp.solutions.face_detection
    face_detector = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5)
    HAS_MEDIAPIPE = True
    logger.info("MediaPipe detector initialised.")
except Exception as e:
    logger.warning(f"MediaPipe initialisation failed, using Haar Cascades: {e}")
    face_detector = None
    # Load Haar cascade
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)

def extract_face_sequence(video_path: str, seq_len: int = SEQUENCE_LENGTH):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    skip = max(1, total_frames // seq_len)
    
    frames = []
    count = 0
    extracted = 0
    
    while cap.isOpened() and extracted < seq_len:
        ret, frame = cap.read()
        if not ret:
            break
            
        if count % skip == 0:
            face_img = None
            try:
                if HAS_MEDIAPIPE and face_detector:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = face_detector.process(rgb_frame)
                    
                    if results.detections:
                        bbox = results.detections[0].location_data.relative_bounding_box
                        h, w, c = frame.shape
                        x, y = int(bbox.xmin * w), int(bbox.ymin * h)
                        width, height = int(bbox.width * w), int(bbox.height * h)
                        
                        x1, y1 = max(0, x), max(0, y)
                        x2, y2 = min(w, x + width), min(h, y + height)
                        face_img = frame[y1:y2, x1:x2]
                else:
                    # Haar Cascade Fallback
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                    if len(faces) > 0:
                        x, y, w, h = faces[0]
                        face_img = frame[y:y+h, x:x+w]
            except Exception as e:
                logger.debug(f"Face detection step failed: {e}")

            if face_img is None or face_img.size == 0:
                h, w, _ = frame.shape
                side = min(h, w)
                face_img = frame[(h-side)//2:(h+side)//2, (w-side)//2:(w+side)//2]

            face_img = cv2.resize(face_img, (IMG_SIZE, IMG_SIZE))
            face_img = face_img / 255.0
            frames.append(face_img)
            extracted += 1
        count += 1
    cap.release()
    
    while len(frames) < seq_len:
        frames.append(frames[-1] if frames else np.zeros((IMG_SIZE, IMG_SIZE, 3)))
            
    return np.array(frames)

def run_inference(video_path: str):
    if not os.path.exists(MODEL_PATH):
        logger.error(f"Model not found at {MODEL_PATH}")
        return

    logger.info(f"Loading model from {MODEL_PATH}...")
    try:
        # Using keras directly often handles Keras 3 .keras files better than tf.keras in some setups
        import keras
        model = keras.models.load_model(MODEL_PATH)
    except Exception as e:
        logger.warning(f"Standard load failed: {e}. Trying alternative load...")
        model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    
    logger.info(f"Processing video: {video_path}")
    sequence = extract_face_sequence(video_path)
    input_data = np.expand_dims(sequence, axis=0) # Add batch dimension
    
    prediction = model.predict(input_data)[0][0]
    is_pain = prediction > 0.5
    label = "PAIN" if is_pain else "NO PAIN"
    confidence = float(prediction if is_pain else 1 - prediction)
    
    # Map to DB enum labels
    # Since model is binary, we map Pain -> Moderate Pain for demonstration
    db_pain_level = "Moderate Pain" if is_pain else "No Pain"
    
    # ─── Database Integration ───────────────────────────────────────────────
    db = SessionLocal()
    try:
        # Check if infant exists, if not create a default one
        infant_id = "INF001"
        infant = db.query(models.Infant).filter(models.Infant.infant_id == infant_id).first()
        if not infant:
            infant = models.Infant(infant_id=infant_id, name="Test Baby", age_days=5)
            db.add(infant)
            db.commit()
            logger.info(f"Created default infant: {infant_id}")

        # Save prediction
        new_pred = models.PainPrediction(
            infant_id=infant_id,
            pain_level=db_pain_level,
            pain_score=float(prediction),
            confidence=confidence,
            image_path=video_path, # Using video path instead of image path
            created_at=datetime.now()
        )
        db.add(new_pred)
        db.commit()
        logger.info(f"Saved prediction to database for infant {infant_id}")
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
    finally:
        db.close()

    print("\n" + "="*40)
    print(f"DATABASE UPDATE: {db_pain_level} saved for INF001")
    print(f"RESULT FOR: {os.path.basename(video_path)}")
    print(f"PREDICTION: {label}")
    print(f"CONFIDENCE: {confidence:.2%}")
    print("="*40 + "\n")

if __name__ == "__main__":
    import sys
    # Default to an example video in the project root; override via CLI
    default_video = str(_PROJECT_ROOT / "hackathon" / "S001_Pain_1_[0]_20s.mp4")
    target_video = sys.argv[1] if len(sys.argv) > 1 else default_video
    run_inference(target_video)
