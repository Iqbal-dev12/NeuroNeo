"""
Pain level constants and mappings for the infant pain detection system.
"""

# Numeric index → human-readable label
PAIN_LEVEL_MAP: dict[int, str] = {
    0: "No Pain",
    1: "Mild Pain",
    2: "Moderate Pain",
    3: "Severe Pain",
}

# Human-readable label → numeric index (reverse map)
PAIN_LEVEL_REVERSE_MAP: dict[str, int] = {v: k for k, v in PAIN_LEVEL_MAP.items()}

# Threshold above which a prediction is considered "severe" and spawns an alert
SEVERE_THRESHOLD_INDEX: int = 3

# Input image size expected by MobileNetV2
MODEL_INPUT_SIZE: tuple[int, int] = (224, 224)

# Confidence below which predictions are flagged as uncertain
LOW_CONFIDENCE_THRESHOLD: float = 0.50

# Number of output classes
NUM_CLASSES: int = 4

# Colour palette for heatmap overlay (BGR OpenCV colours)
PAIN_LEVEL_COLORS: dict[str, tuple[int, int, int]] = {
    "No Pain":       (0, 255, 0),    # Green
    "Mild Pain":     (0, 255, 255),  # Yellow
    "Moderate Pain": (0, 165, 255),  # Orange
    "Severe Pain":   (0, 0, 255),    # Red
}
