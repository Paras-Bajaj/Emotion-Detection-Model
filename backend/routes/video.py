from flask import Blueprint, request, jsonify
import os
from utils.emotion import analyze_video
from utils.db import results
from datetime import datetime
from utils.auth_middleware import verify_token

video_bp = Blueprint('video', __name__)

UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@video_bp.route('/upload', methods=['POST'])
def upload_video():

    # 🔐 VERIFY TOKEN
    user, error, status = verify_token()
    if error:
        return error, status

    # CHECK FILE
    if 'video' not in request.files:
        return jsonify({"msg": "No video uploaded"}), 400

    file = request.files['video']

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    print("Video saved:", filepath)

    # ANALYZE VIDEO
    try:
        emotions, summary = analyze_video(filepath)
    except RuntimeError as exc:
        return jsonify({"msg": str(exc)}), 503

    # STORE IN DB
    results.insert_one({
        "user": user["email"],
        "video": file.filename,
        "emotions": emotions,
        "summary": summary,
        "timestamp": datetime.now()
    })

    return jsonify({
        "message": "Analysis complete",
        "summary": summary,
        "emotions": emotions
    })