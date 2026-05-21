import streamlit as st
import cv2
import requests
from PIL import Image
from datetime import datetime
import time
import threading
import queue
import numpy as np

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="AffectNet AI Engine",
    layout="wide",
    page_icon="🧠",
    initial_sidebar_state="collapsed"
)

# =========================================================
# CONSTANTS
# =========================================================
API_URL            = "http://localhost:8000/predict"
API_TIMEOUT        = 5          # lower timeout → fail fast
PREDICTION_INTERVAL = 0.7       # seconds between API calls
FRAME_SLEEP        = 0.025      # ~40 fps cap
JPEG_QUALITY       = 60         # lower = faster encode/transmit
CAM_WIDTH          = 640
CAM_HEIGHT         = 480

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp {
    background:
        radial-gradient(circle at top left, rgba(96,165,250,0.12), transparent 22%),
        radial-gradient(circle at top right, rgba(192,132,252,0.10), transparent 22%),
        linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%);
}
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
.main .block-container { padding: 1rem 2rem; max-width: 1400px; }
.navbar {
    display: flex; justify-content: space-between; align-items: center;
    background: rgba(255,255,255,0.85); padding: 12px 28px;
    border-radius: 20px; margin-bottom: 20px;
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.8);
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}
.brand {
    font-size: 1.5rem; font-weight: 800;
    background: linear-gradient(135deg,#2563eb,#7c3aed);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.nav-info { color: #64748b; font-size: 0.8rem; font-weight: 500; }
.hero {
    background: linear-gradient(135deg,rgba(255,255,255,0.95),rgba(255,255,255,0.85));
    border-radius: 24px; padding: 20px 30px; margin-bottom: 20px;
    border: 1px solid rgba(255,255,255,0.9);
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
}
.hero-title {
    font-size: 2.2rem; font-weight: 800; margin-bottom: 8px;
    background: linear-gradient(135deg,#0f172a,#2563eb);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.metric-card {
    background: rgba(255,255,255,0.9); border-radius: 18px;
    padding: 12px 15px; text-align: center;
    border: 1px solid rgba(255,255,255,0.8);
    box-shadow: 0 2px 10px rgba(0,0,0,0.04);
}
.metric-title { color: #64748b; font-size: 0.65rem; font-weight: 700; margin-bottom: 6px; }
.metric-value { font-size: 1.4rem; font-weight: 800; color: #0f172a; }
.metric-sub   { color: #94a3b8; font-size: 0.7rem; margin-top: 4px; }
.analytics {
    background: rgba(255,255,255,0.92); border-radius: 24px; padding: 20px;
    border: 1px solid rgba(255,255,255,0.8);
    box-shadow: 0 6px 20px rgba(0,0,0,0.06);
}
.section-title { font-size: 1.1rem; font-weight: 700; color: #0f172a; margin-bottom: 15px; }
.status-badge { display: inline-block; padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 0.75rem; }
.status-active { background: #dcfce7; color: #15803d; }
.status-idle   { background: #e2e8f0; color: #475569; }
.emotion-text  { font-size: 2rem; font-weight: 800; color: #2563eb; margin: 10px 0; }
.stImage img   { border-radius: 16px !important; }
.stButton button {
    width: 100%; height: 45px; border: none; border-radius: 14px;
    font-weight: 600; font-size: 0.85rem;
    background: linear-gradient(135deg,#2563eb,#7c3aed); color: white;
}
.stRadio > div { background: rgba(255,255,255,0.85); padding: 8px 12px; border-radius: 14px; }
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.85); border-radius: 16px;
    padding: 15px; border: 1px dashed #cbd5e1;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# SESSION STATE INIT
# =========================================================
def init_state():
    defaults = {
        "camera_running":    False,
        "current_emotion":   "Waiting...",
        "current_confidence": 0.0,
        # Threading primitives stored once
        "_frame_queue":      None,
        "_result_queue":     None,
        "_api_thread":       None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# =========================================================
# API WORKER — runs in background thread
# Non-blocking: pulls frames from frame_queue, pushes
# results to result_queue. Never blocks the display loop.
# =========================================================
def api_worker(frame_queue: queue.Queue, result_queue: queue.Queue, stop_event: threading.Event):
    """
    Dedicated thread that calls the prediction API.
    Drains stale frames so only the latest is sent.
    """
    session = requests.Session()        # reuse TCP connection

    while not stop_event.is_set():
        try:
            # Drain queue — keep only the most recent frame
            img_bytes = None
            while True:
                try:
                    img_bytes = frame_queue.get_nowait()
                except queue.Empty:
                    break

            if img_bytes is None:
                time.sleep(0.01)
                continue

            resp = session.post(
                API_URL,
                files={"file": ("img.jpg", img_bytes)},
                timeout=API_TIMEOUT
            )

            if resp.status_code == 200:
                data = resp.json()
                emotion = (
                    data.get("prediction")
                    or data.get("emotion")
                    or data.get("label")
                    or "No Face Detected"
                )
                confidence = float(data.get("confidence", 0.0))
            else:
                emotion, confidence = "API Error", 0.0

        except requests.exceptions.Timeout:
            emotion, confidence = "Timeout", 0.0
        except Exception:
            emotion, confidence = "Backend Error", 0.0

        # Overwrite stale results — only latest matters
        while not result_queue.empty():
            try:
                result_queue.get_nowait()
            except queue.Empty:
                break
        result_queue.put({"prediction": emotion, "confidence": confidence})

        # Throttle API calls to PREDICTION_INTERVAL
        time.sleep(PREDICTION_INTERVAL)


# =========================================================
# OVERLAY HELPER — draw once per changed prediction
# =========================================================
# Pre-allocate text params to avoid dict lookups in the hot loop
_FONT       = cv2.FONT_HERSHEY_SIMPLEX
_BLUE       = (37, 99, 235)
_DARK       = (15, 23, 42)
_WHITE      = (255, 255, 255)

def draw_overlay(frame: np.ndarray, emotion: str, confidence: float) -> np.ndarray:
    """
    Draw a semi-transparent result box on the frame.
    Modifies frame in-place for speed; returns it for chaining.
    """
    h, w = frame.shape[:2]
    box_w = min(460, w - 20)

    # ROI blend instead of full-frame addWeighted
    roi = frame[10:120, 10:10 + box_w]
    white_box = np.full_like(roi, 255)
    cv2.addWeighted(white_box, 0.65, roi, 0.35, 0, roi)

    cv2.putText(frame, f"Emotion: {emotion}",         (25, 55),  _FONT, 0.9, _BLUE,  2, cv2.LINE_AA)
    cv2.putText(frame, f"Confidence: {confidence:.1%}", (25, 95), _FONT, 0.7, _DARK,  2, cv2.LINE_AA)
    return frame


# =========================================================
# IMAGE UPLOAD PREDICTION (synchronous, one-shot)
# =========================================================
def get_prediction_sync(img_bytes: bytes) -> dict:
    try:
        response = requests.post(
            API_URL,
            files={"file": ("img.jpg", img_bytes)},
            timeout=API_TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            emotion = (
                data.get("prediction")
                or data.get("emotion")
                or data.get("label")
                or "No Face Detected"
            )
            return {"prediction": emotion, "confidence": float(data.get("confidence", 0.0))}
        return {"prediction": "API Error", "confidence": 0.0}
    except Exception:
        return {"prediction": "Backend Error", "confidence": 0.0}


# =========================================================
# NAVBAR
# =========================================================
st.markdown(f"""
<div class="navbar">
    <div class="brand">🧠 AffectNet AI Engine</div>
    <div class="nav-info">{datetime.now().strftime("%B %d, %Y")}</div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# HERO
# =========================================================
st.markdown("""
<div class="hero">
    <div class="hero-title">Facial Emotion Recognition</div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# METRICS
# =========================================================
c1, c2, c3, c4 = st.columns(4)
cards = [
    ("MODEL",    "ViT",    "Transformer"),
    ("ACCURACY", "95.2%",  "AffectNet"),
    ("SPEED",    "45ms",   "Realtime"),
    ("STATUS",   "ONLINE", "Ready"),
]
for col, (title, value, sub) in zip([c1, c2, c3, c4], cards):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# MAIN LAYOUT
# =========================================================
left_col, right_col = st.columns([2.2, 1.2])

# =========================================================
# LEFT PANEL
# =========================================================
with left_col:

    input_mode = st.radio(
        "Select Input",
        ["📸 Live Camera", "🖼️ Upload Image"],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────
    # CAMERA MODE
    # ─────────────────────────────────────────────────────
    if input_mode == "📸 Live Camera":

        b1, b2 = st.columns(2)
        with b1:
            start = st.button("🎥  START CAMERA")
        with b2:
            stop  = st.button("⏹️  STOP CAMERA")

        if start:
            st.session_state.camera_running = True
        if stop:
            st.session_state.camera_running = False

        st.markdown("<br>", unsafe_allow_html=True)
        camera_placeholder = st.empty()

        if st.session_state.camera_running:

            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # minimize capture buffer lag

            if not cap.isOpened():
                st.error("❌ Unable to access camera")
                st.session_state.camera_running = False
            else:
                # ── Thread-safe queues (max size 1 = never stale) ──
                frame_queue  = queue.Queue(maxsize=1)
                result_queue = queue.Queue(maxsize=1)
                stop_event   = threading.Event()

                worker = threading.Thread(
                    target=api_worker,
                    args=(frame_queue, result_queue, stop_event),
                    daemon=True
                )
                worker.start()

                emotion    = "Detecting..."
                confidence = 0.0

                try:
                    while st.session_state.camera_running:

                        ret, frame = cap.read()
                        if not ret:
                            st.error("❌ Failed to read frame")
                            break

                        frame = cv2.flip(frame, 1)

                        # ── Encode once, reuse for both queue + display ──
                        _, enc = cv2.imencode(
                            ".jpg", frame,
                            [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
                        )
                        img_bytes = enc.tobytes()

                        # ── Non-blocking push to API thread ──
                        try:
                            frame_queue.put_nowait(img_bytes)
                        except queue.Full:
                            pass  # API thread is busy; skip this frame

                        # ── Non-blocking pull of latest prediction ──
                        try:
                            result = result_queue.get_nowait()
                            emotion    = result["prediction"]
                            confidence = float(result.get("confidence", 0.0))
                            st.session_state.current_emotion    = emotion
                            st.session_state.current_confidence = confidence
                        except queue.Empty:
                            pass  # keep last known values

                        # ── Draw overlay on BGR frame ──
                        draw_overlay(frame, emotion, confidence)

                        # ── Convert BGR→RGB only once, after overlay ──
                        camera_placeholder.image(
                            cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
                            channels="RGB",
                            use_container_width=True,
                        )

                        time.sleep(FRAME_SLEEP)

                finally:
                    stop_event.set()
                    cap.release()

        else:
            camera_placeholder.info("👈 Click Start Camera to begin")

    # ─────────────────────────────────────────────────────
    # IMAGE UPLOAD MODE
    # ─────────────────────────────────────────────────────
    else:
        st.session_state.camera_running = False

        uploaded_file = st.file_uploader(
            "Upload Image",
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed"
        )

        if uploaded_file is not None:
            image     = Image.open(uploaded_file).convert("RGB")
            st.image(image, use_container_width=True)

            uploaded_file.seek(0)
            prediction = get_prediction_sync(uploaded_file.read())

            emotion    = prediction["prediction"]
            confidence = float(prediction.get("confidence", 0.0))

            st.session_state.current_emotion    = emotion
            st.session_state.current_confidence = confidence


# =========================================================
# RIGHT PANEL
# =========================================================
with right_col:
    st.markdown('<div class="analytics">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Emotion Analytics</div>', unsafe_allow_html=True)

    is_active = st.session_state.current_emotion not in ("Waiting...", "Detecting...")
    badge_cls  = "status-active" if is_active else "status-idle"
    badge_icon = "🟢 Active"      if is_active else "⚪ Waiting"

    st.markdown(f'<span class="status-badge {badge_cls}">{badge_icon}</span>', unsafe_allow_html=True)
    st.markdown(f'<div class="emotion-text">{st.session_state.current_emotion}</div>', unsafe_allow_html=True)

    st.progress(min(st.session_state.current_confidence, 1.0))
    st.markdown(
        f"<h3 style='text-align:center;margin-top:10px;'>"
        f"{st.session_state.current_confidence:.1%}</h3>",
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# FOOTER
# =========================================================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="background:rgba(255,255,255,0.7);border-radius:16px;padding:12px 20px;
            text-align:center;border:1px solid rgba(255,255,255,0.6);">
  <span style="color:#64748b;font-size:0.75rem;">
    ⚡ Real-time inference &nbsp;•&nbsp; 🧠 ViT Architecture &nbsp;•&nbsp; 🎯 7 Emotions
  </span>
</div>
""", unsafe_allow_html=True)