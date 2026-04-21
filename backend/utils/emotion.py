93% of storage used … If you run out, you can't create, edit and upload files. Share 100 GB of storage with your family members for ₹59 for 1 month ₹130.
from collections import Counter


def analyze_video(video_path):
    """
    Returns:
        emotions list + dominant emotion
    """

    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("opencv-python is not installed") from exc

    try:
        from deepface import DeepFace
    except ImportError as exc:
        raise RuntimeError("deepface is not installed") from exc

    emotions = []
    cap = cv2.VideoCapture(video_path)
    frame_count = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        frame_count += 1

        if frame_count % 20 != 0:
            continue

        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            result = DeepFace.analyze(
                rgb_frame,
                actions=['emotion'],
                enforce_detection=False
            )

            if isinstance(result, list):
                emotion = result[0]['dominant_emotion']
            else:
                emotion = result['dominant_emotion']

            print("Frame emotion:", emotion)
            emotions.append(emotion)
        except Exception as exc:
            print("Error processing frame:", exc)
            continue

    cap.release()

    if not emotions:
        return [], "No emotion detected"

    dominant_emotion = Counter(emotions).most_common(1)[0][0]
    print("\nFinal Dominant Emotion:", dominant_emotion)
    return emotions, dominant_emotion