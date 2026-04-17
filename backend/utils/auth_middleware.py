import jwt
from flask import request, jsonify

SECRET_KEY = "secret123"


def verify_token():
    token = request.headers.get("Authorization")

    if not token:
        return None, jsonify({"msg": "Token missing"}), 401

    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded, None, None

    except Exception as e:
        print("JWT ERROR:", e)
        return None, jsonify({"msg": "Invalid token"}), 401