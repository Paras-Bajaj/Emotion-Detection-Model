from flask import request, jsonify
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from utils.tokens import TOKEN_MAX_AGE_SECONDS, get_secret_key

serializer = URLSafeTimedSerializer(get_secret_key())


def verify_token():
    token = request.headers.get("Authorization")

    if not token:
        return None, jsonify({"msg": "Token missing"}), 401

    try:
        decoded = serializer.loads(token, max_age=TOKEN_MAX_AGE_SECONDS)
        return decoded, None, None
    except SignatureExpired:
        return None, jsonify({"msg": "Token expired"}), 401
    except BadSignature as exc:
        print("TOKEN ERROR:", exc)
        return None, jsonify({"msg": "Invalid token"}), 401