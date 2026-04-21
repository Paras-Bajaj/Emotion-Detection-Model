93% of storage used … If you run out, you can't create, edit and upload files. Share 100 GB of storage with your family members for ₹59 for 1 month ₹130.
from flask import Flask
from flask_cors import CORS
from routes.auth import auth_bp
from routes.video import video_bp
from routes.webcam import webcam_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(auth_bp)
app.register_blueprint(video_bp)
app.register_blueprint(webcam_bp)

@app.route('/')
def home():
    return {"message": "Emotion Detection API Running"}

if __name__ == "__main__":
    app.run(debug=True)