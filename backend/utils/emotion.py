import cv2
from deepface import DeepFace
from collections import Counter


def analyze_video(video_path):
    """
    Returns:
        emotions list + dominant emotion
    """

    emotions = []

    cap = cv2.VideoCapture(video_path)

    frame_count = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        frame_count += 1

        # 🔥 keep your original frame logic (every 10th frame)
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

            # ✅ PRINT (as you want)
            print("Frame emotion:", emotion)

            emotions.append(emotion)

        except Exception as e:
            print("Error processing frame:", e)
            continue

    cap.release()

    # 🔥 handle no detection
    if not emotions:
        return [], "No emotion detected"

    # 🔥 dominant emotion
    dominant_emotion = Counter(emotions).most_common(1)[0][0]

    print("\nFinal Dominant Emotion:", dominant_emotion)

    return emotions, dominant_emotion