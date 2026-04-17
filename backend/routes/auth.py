from flask import Blueprint, request, jsonify
from utils.db import users
import bcrypt
import jwt
import datetime

auth_bp = Blueprint('auth', __name__)

SECRET_KEY = "secret123"


# 🔐 SIGNUP
@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json

    email = data.get("email")
    password = data.get("password")

    if users.find_one({"email": email}):
        return jsonify({"msg": "User already exists"}), 400

    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    users.insert_one({
        "email": email,
        "password": hashed_password
    })

    return jsonify({"msg": "Signup successful"})


# 🔐 LOGIN
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json

    email = data.get("email")
    password = data.get("password")

    user = users.find_one({"email": email})

    if not user:
        return jsonify({"msg": "User not found"}), 404

    if not bcrypt.checkpw(password.encode(), user["password"]):
        return jsonify({"msg": "Invalid password"}), 401

    # 🔥 CREATE TOKEN
    token = jwt.encode({
        "email": email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }, SECRET_KEY, algorithm="HS256")

    return jsonify({
        "msg": "Login successful",
        "token": token
    })