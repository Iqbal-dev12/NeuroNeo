"""
train_model.py
Training pipeline for Infant Pain Detection using CNN-LSTM.

Architecture:
- MobileNetV2 (Frozen backbone) for spatial feature extraction.
- LSTM layer for temporal sequence analysis.
- Dense layers for 2-class (Pain vs No-Pain) classification.
"""

import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, Sequential
from sklearn.model_selection import train_test_split
from loguru import logger
import mediapipe as mp

# ─── Configuration ───────────────────────────────────────────────────────────

DATASET_DIR = "C:/Users/rehan/OneDrive/Desktop/hackathon/dataset/dataset"
MODEL_SAVE_PATH = "C:/Users/rehan/OneDrive/Desktop/hackathon/backend/model/pain_video_model.keras"

# Video params
IMG_SIZE = 224
SEQUENCE_LENGTH = 16  # Frames per sequence
BATCH_SIZE = 4
EPOCHS = 10

# MediaPipe for face detection
mp_face_detection = mp.solutions.face_detection
face_detector = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5)

# ─── Preprocessing Helpers ───────────────────────────────────────────────────

def extract_face_sequence(video_path: str, seq_len: int = SEQUENCE_LENGTH):
    """
    Extracts a sequence of cropped faces from a video.
    """
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Calculate skip factor to get even distribution
    skip = max(1, total_frames // seq_len)
    
    frames = []
    count = 0
    extracted = 0
    
    while cap.isOpened() and extracted < seq_len:
        ret, frame = cap.read()
        if not ret:
            break
            
        if count % skip == 0:
            # Face detection
            face_img = None
            try:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_detector.process(rgb_frame)
                
                if results.detections:
                    # Use the first detection
                    bbox = results.detections[0].location_data.relative_bounding_box
                    h, w, c = frame.shape
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)
                    
                    # Padding
                    pad_w = int(width * 0.1)
                    pad_h = int(height * 0.1)
                    
                    x1 = max(0, x - pad_w)
                    y1 = max(0, y - pad_h)
                    x2 = min(w, x + width + pad_w)
                    y2 = min(h, y + height + pad_h)
                    
                    face_img = frame[y1:y2, x1:x2]
            except Exception as e:
                # Log error only once per video
                if extracted == 0:
                    logger.warning(f"Face detector failed (Protobuf conflict likely): {e}. Using center crop.")
            
            # Fallback to center crop if no face detected
            if face_img is None or face_img.size == 0:
                h, w, _ = frame.shape
                side = min(h, w)
                face_img = frame[(h-side)//2:(h+side)//2, (w-side)//2:(w+side)//2]

            face_img = cv2.resize(face_img, (IMG_SIZE, IMG_SIZE))
            face_img = face_img / 255.0  # Normalise
            frames.append(face_img)
            extracted += 1
            
        count += 1
        
    cap.release()
    
    # If we didn't get enough frames, pad with zeros or repeat
    while len(frames) < seq_len:
        if len(frames) > 0:
            frames.append(frames[-1])
        else:
            frames.append(np.zeros((IMG_SIZE, IMG_SIZE, 3)))
            
    return np.array(frames)

# ─── Data Loading ────────────────────────────────────────────────────────────

def load_dataset():
    X = []
    y = []
    
    classes = {
        "Pain": 1,
        "No-pain": 0
    }
    
    for class_name, label in classes.items():
        class_path = os.path.join(DATASET_DIR, class_name)
        logger.info(f"Loading class: {class_name}")
        
        # Handle subdirs (like No-pain/rest, Pain/...)
        for root, dirs, files in os.walk(class_path):
            for file in files:
                if file.endswith((".mp4", ".avi", ".mov")):
                    video_path = os.path.join(root, file)
                    logger.debug(f"Processing: {file}")
                    
                    try:
                        seq = extract_face_sequence(video_path)
                        X.append(seq)
                        y.append(label)
                    except Exception as e:
                        logger.error(f"Error processing {file}: {e}")
                        
    return np.array(X), np.array(y)

# ─── Model Architecture ──────────────────────────────────────────────────────

def build_model():
    # MobileNetV2 for spatial features
    backbone = tf.keras.applications.MobileNetV2(
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        include_top=False,
        weights='imagenet'
    )
    backbone.trainable = False
    
    model = Sequential([
        layers.TimeDistributed(backbone, input_shape=(SEQUENCE_LENGTH, IMG_SIZE, IMG_SIZE, 3)),
        layers.TimeDistributed(layers.GlobalAveragePooling2D()),
        layers.LSTM(64, return_sequences=False),
        layers.Dropout(0.5),
        layers.Dense(32, activation='relu'),
        layers.Dense(1, activation='sigmoid')
    ])
    
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    return model

# ─── Main Execution ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("Starting dataset loading (this may take a while)...")
    X, y = load_dataset()
    logger.info(f"Dataset loaded. Total sequences: {len(X)}")
    
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    
    logger.info("Building model...")
    model = build_model()
    model.summary()
    
    logger.info("Starting training...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE
    )
    
    logger.info(f"Saving model to {MODEL_SAVE_PATH}")
    os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
    model.save(MODEL_SAVE_PATH)
    
    logger.info("Training complete.")
