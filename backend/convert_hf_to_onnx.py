import os
import torch
from transformers import AutoModelForImageClassification

HF_MODEL_NAME = "dima806/facial_emotions_image_detection"
OUTPUT_ONNX_PATH = "model_store/emotion_model.onnx"

def convert_huggingface_to_onnx():
    print(f"⏳ Downloading '{HF_MODEL_NAME}' layer architecture from Hugging Face...")
    
    # Download weights and model configuration setup
    model = AutoModelForImageClassification.from_pretrained(HF_MODEL_NAME)
    model.eval()

    # ViT expects a standard (Batch Size, Channels, Height, Width) shape
    # 3-channel RGB images resized precisely to 224x224 pixels
    dummy_input = torch.randn(1, 3, 224, 224, dtype=torch.float32)

    os.makedirs(os.path.dirname(OUTPUT_ONNX_PATH), exist_ok=True)
    print(f"📦 Compiling transformer layers into production ONNX graph at: {OUTPUT_ONNX_PATH}")
    
    # Export the computational graph
    torch.onnx.export(
        model,
        (dummy_input,),
        OUTPUT_ONNX_PATH,
        export_params=True,
        opset_version=14,  # High-level attention layers need opset 14+ matching ViT specs
        do_constant_folding=True,
        input_names=['pixel_values'],  # Hugging Face models expect 'pixel_values' as their dictionary key
        output_names=['logits'],
        dynamic_axes={
            'pixel_values': {0: 'batch_size'},
            'logits': {0: 'batch_size'}
        }
    )
    print("🚀 ONNX compilation complete! Weights frozen safely inside model_store/")

if __name__ == "__main__":
    convert_huggingface_to_onnx()