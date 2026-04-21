93% of storage used … If you run out, you can't create, edit and upload files. Share 100 GB of storage with your family members for ₹59 for 1 month ₹130.
from flask import Blueprint, Response

webcam_bp = Blueprint('webcam', __name__)


def generate_frames():
    try:
        import cv2
    except ImportError:
        yield b'--frame\r\nContent-Type: text/plain\r\n\r\nopencv-python is not installed\r\n'
        return

    try:
        from deepface import DeepFace
    except ImportError:
        yield b'--frame\r\nContent-Type: text/plain\r\n\r\ndeepface is not installed\r\n'
        return

    cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success:
            break

        try:
            result = DeepFace.analyze(
                frame,
                actions=['emotion'],
                enforce_detection=False
            )

            emotion = result.get('dominant_emotion') if isinstance(result, dict) else None
            if not emotion:
                emotion = "unknown"

            cv2.putText(
                frame,
                emotion,
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )
        except Exception:
            pass

        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               frame_bytes + b'\r\n')


@webcam_bp.route('/video_feed')
def video_feed():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )