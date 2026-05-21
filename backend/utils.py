import cv2
import numpy as np

# Exact index configuration pulled from dima806/facial_emotions_image_detection config mapping
EMOTION_LABELS = {
    0: "Sad",
    1: "Disgust",
    2: "Angry",
    3: "Neutral",
    4: "Fear",
    5: "Surprise",
    6: "Happy"
}

def preprocess_image(image_matrix: np.ndarray) -> np.ndarray:
    """Transforms raw BGR camera frames to match Hugging Face ViT requirements."""
    if image_matrix is None:
        raise ValueError("Invalid frame matrix received.")

    try:
        # 1. Convert OpenCV default BGR representation to RGB layout
        rgb_image = cv2.cvtColor(image_matrix, cv2.COLOR_BGR2RGB)
        
        # 2. Resize to standard square dimensions matching transformer configurations
        resized = cv2.resize(rgb_image, (224, 224))
        
        # 3. Convert to float array scaled exactly between [0.0, 1.0]
        normalized = resized.astype(np.float32) / 255.0
        
        # 4. Standard Hugging Face ImageNet-style normalization tensors
        mean = np.array([0.5, 0.5, 0.5], dtype=np.float32)
        std = np.array([0.5, 0.5, 0.5], dtype=np.float32)
        standardized = (normalized - mean) / std

        # 5. Transpose dimensions from HWC (Height, Width, Channels) to CHW format
        chw = np.transpose(standardized, (2, 0, 1))
        
        # 6. Insert batch dimension wrapper -> (1, 3, 224, 224)
        return np.expand_dims(chw, axis=0)
        
    except Exception as e:
        raise ValueError(f"Transformer preprocessing failure: {str(e)}")