93% of storage used … If you run out, you can't create, edit and upload files. Share 100 GB of storage with your family members for ₹59 for 1 month ₹130.
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import URLSafeTimedSerializer

from utils.db import users
from utils.tokens import get_secret_key

auth_bp = Blueprint('auth', __name__)
serializer = URLSafeTimedSerializer(get_secret_key())


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json(silent=True) or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"msg": "Email and password are required"}), 400

    if users.find_one({"email": email}):
        return jsonify({"msg": "User already exists"}), 400

    users.insert_one({
        "email": email,
        "password": generate_password_hash(password)
    })

    return jsonify({"msg": "Signup successful"})


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"msg": "Email and password are required"}), 400

    user = users.find_one({"email": email})

    if not user:
        return jsonify({"msg": "User not found"}), 404

    if not check_password_hash(user["password"], password):
        return jsonify({"msg": "Invalid password"}), 401

    token = serializer.dumps({"email": email})

    return jsonify({
        "msg": "Login successful",
        "token": token
    })