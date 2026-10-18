"""
services/heatmap_service.py
Grad-CAM explainability for the pain classification model.

The implementation works with any Keras model that has a convolutional
backbone.  For MobileNetV2 we target the last convolutional layer
(`out_relu` / `Conv_1_bn`).
"""

from typing import Optional

import cv2
import numpy as np
import tensorflow as tf
from loguru import logger


class GradCAM:
    """
    Gradient-weighted Class Activation Mapping (Grad-CAM).

    Parameters
    ----------
    model      : Compiled Keras model
    last_conv_layer_name : Name of the last conv layer to hook into
    """

    def __init__(self, model: tf.keras.Model, last_conv_layer_name: str = "out_relu") -> None:
        self.model = model
        self.last_conv_layer_name = last_conv_layer_name

        # Build sub-model that outputs (conv_features, predictions)
        self._grad_model = self._build_grad_model()
        logger.info("GradCAM initialised with conv layer '{}'", last_conv_layer_name)

    # ── Public API ──────────────────────────────────────────────────────────

    def generate_heatmap(
        self,
        preprocessed_input: np.ndarray,   # shape (1, 224, 224, 3)
        class_idx: int,
        alpha: float = 0.4,
        original_bgr: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Generate a Grad-CAM heatmap and optionally overlay it on *original_bgr*.

        Returns
        -------
        np.ndarray : BGR overlay image (same size as *original_bgr* if supplied,
                     otherwise 224×224).
        """
        heatmap = self._compute_heatmap(preprocessed_input, class_idx)

        if original_bgr is not None:
            target_h, target_w = original_bgr.shape[:2]
        else:
            target_h, target_w = 224, 224

        # Resize heatmap to target size
        heatmap_resized = cv2.resize(heatmap, (target_w, target_h))

        # Normalise to [0, 255] and apply colour map
        heatmap_uint8 = np.uint8(255 * heatmap_resized)
        heatmap_colour = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

        if original_bgr is not None:
            overlay = cv2.addWeighted(original_bgr, 1 - alpha, heatmap_colour, alpha, 0)
        else:
            overlay = heatmap_colour

        logger.debug("Grad-CAM heatmap generated for class_idx={}", class_idx)
        return overlay

    # ── Internals ────────────────────────────────────────────────────────────

    def _build_grad_model(self) -> tf.keras.Model:
        """
        Build a sub-model exposing the target conv layer's output alongside
        the final predictions.
        """
        conv_layer = None
        
        # 1. Try direct lookup or nested lookup
        def find_layer(model, name):
            try:
                return model.get_layer(name)
            except ValueError:
                for l in model.layers:
                    # Look inside TimeDistributed or nested models
                    inner = getattr(l, 'layer', l)
                    if hasattr(inner, 'get_layer'):
                        try:
                            return inner.get_layer(name)
                        except ValueError:
                            pass
            return None

        conv_layer = find_layer(self.model, self.last_conv_layer_name)

        # 2. Try common MobileNetV2 alternative names in nested models
        if conv_layer is None:
            for alt in ("out_relu", "Conv_1_bn", "block_16_project_BN", "Conv_1"):
                conv_layer = find_layer(self.model, alt)
                if conv_layer:
                    self.last_conv_layer_name = alt
                    break

        # 3. Fallback: find the VERY LAST layer that looks like a Conv or ReLU
        if conv_layer is None:
            logger.warning("Target layer '{}' not found. Searching for last Conv/ReLU layer...", self.last_conv_layer_name)
            def search_last_conv(model):
                for layer in reversed(model.layers):
                    inner = getattr(layer, 'layer', layer)
                    if hasattr(inner, 'layers'):
                        res = search_last_conv(inner)
                        if res: return res
                    if any(t in layer.name.lower() for t in ("conv", "relu", "bn")):
                        return layer
                return None
            
            conv_layer = search_last_conv(self.model)
            if conv_layer:
                self.last_conv_layer_name = conv_layer.name

        if conv_layer is None:
            raise ValueError(
                "Could not find a suitable conv layer for Grad-CAM. "
                "Please specify 'last_conv_layer_name' explicitly."
            )

        logger.info("Grad-CAM targeting layer: {}", self.last_conv_layer_name)

        # Try to get output tensor safely using multiple strategies for Keras 3 compatibility
        output_tensor = None
        
        # Strategy A: Property access (standard)
        if output_tensor is None:
            try:
                output_tensor = conv_layer.output
            except (AttributeError, ValueError):
                pass
        
        # Strategy B: Node-based access
        if output_tensor is None:
            try:
                output_tensor = conv_layer.get_output_at(0)
            except Exception:
                pass
        
        # Strategy C: Internal property access
        if output_tensor is None:
            try:
                 # Some Keras 3 layers hide output_tensors
                output_tensor = conv_layer.output_tensors[0]
            except Exception:
                pass

        if output_tensor is None:
            raise ValueError(f"Could not access output tensor for layer '{conv_layer.name}'.")

        return tf.keras.Model(
            inputs=self.model.inputs,
            outputs=[output_tensor, self.model.output],
        )

    def _compute_heatmap(
        self, img_array: np.ndarray, class_idx: int
    ) -> np.ndarray:
        """
        Core Grad-CAM computation.

        1. Forward pass through grad_model
        2. Compute gradient of class score w.r.t. conv feature map
        3. Pool gradients across spatial dims → channel weights
        4. Weighted sum of feature maps → heatmap
        5. ReLU + normalise
        """
        img_tensor = tf.cast(img_array, tf.float32)

        with tf.GradientTape() as tape:
            tape.watch(img_tensor)
            conv_outputs, predictions = self._grad_model(img_tensor)
            class_score = predictions[:, class_idx]

        # Gradients of the class score w.r.t. conv layer output
        grads = tape.gradient(class_score, conv_outputs)

        # Handle sequence dimension (1, 16, 7, 7, 1280) -> (1, 7, 7, 1280)
        if len(conv_outputs.shape) == 5:
            conv_outputs = conv_outputs[:, 0, :, :, :]
            grads = grads[:, 0, :, :, :]

        # Pool gradients over spatial dimensions
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))    # (c,)

        conv_outputs = conv_outputs[0]                          # (h, w, c)

        # Weighted combination of feature maps
        heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]  # (h, w, 1)
        heatmap = tf.squeeze(heatmap)                           # (h, w)

        # ReLU: keep only positive influences
        heatmap = tf.nn.relu(heatmap)

        # Normalise to [0, 1]
        heatmap = heatmap.numpy()
        max_val = heatmap.max()
        if max_val > 0:
            heatmap /= max_val

        return heatmap.astype(np.float32)
