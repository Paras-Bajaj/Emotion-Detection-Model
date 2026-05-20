import os
import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, HTTPException, UploadFile, File
import cv2

from src.inference.utils import preprocess_image, EMOTION_LABELS

app = FastAPI(title="Vision-Based Emotion Recognition Engine", version="2.0")

MODEL_PATH = "model_store/emotion_model.onnx"

if not os.path.exists(MODEL_PATH):
    raise RuntimeError(f"Compiled model target not found at {MODEL_PATH}. Run 'python convert_hf_to_onnx.py' first.")

# Start up inference execution tracking session
print("🧠 Initializing production ONNX Runtime session pool...")
ort_session = ort.InferenceSession(MODEL_PATH, providers=['CPUExecutionProvider'])

@app.post("/predict")
async def predict_emotion(file: UploadFile = File(...)):
    """Receives file streams, handles visual transformations, and returns emotion vectors."""
    try:
        # Read incoming raw image frame bytes
        file_bytes = await file.read()
        nparr = np.frombuffer(file_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid file data structure received.")

        # Transform using transformer pre-processing guidelines
        tensor_data = preprocess_image(frame)

        # Query model layer labels dynamically to route input to 'pixel_values'
        input_name = ort_session.get_inputs()[0].name
        raw_logits = ort_session.run(None, {input_name: tensor_data})[0]

        # Process logit array arrays through Softmax scaling
        probabilities = np.exp(raw_logits) / np.sum(np.exp(raw_logits), axis=1, keepdims=True)
        max_index = int(np.argmax(probabilities))
        confidence_score = float(probabilities[0][max_index])

        return {
            "success": True,
            "prediction": EMOTION_LABELS.get(max_index, "Unknown"),
            "confidence": round(confidence_score, 4),
            "distribution": {EMOTION_LABELS[i]: float(probabilities[0][i]) for i in range(len(EMOTION_LABELS))}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference Engine Crash: {str(e)}")

@app.get("/health")
def health_check():
    return {"status": "active", "engine": "ONNX-Transformer", "classes": list(EMOTION_LABELS.values())}