# ==========================================
# STAGE 1: Dependency Compilation Builder
# ==========================================
FROM python:3.10-slim AS builder

WORKDIR /app

# Install native system compilers needed for complex wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Compile and isolate Python wheels safely inside the user profile directory
RUN pip install --no-cache-dir --user -r requirements.txt

# ==========================================
# STAGE 2: Lightweight Production Runtime
# ==========================================
FROM python:3.10-slim

WORKDIR /app

# Inject compiled library assets from Stage 1
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Create the internal path expected by the FastAPI engine state variables
RUN mkdir -p model_store

# Copy source scripts and bundle the core model weights file
COPY ./src /app/src
COPY ./model_store/emotion_model.onnx /app/model_store/emotion_model.onnx

EXPOSE 8000

# Run the asynchronous ASGI server bound to all interfaces
CMD ["uvicorn", "src.inference.app:app", "--host", "0.0.0.0", "--port", "8000"]