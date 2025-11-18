# login.py
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
import jwt
import datetime
import os

login_bp = Blueprint('login', __name__)

USERS = {
    "admin": {
        "password_hash": "scrypt:32768:8:1$jWBrkXvih2duabaj$acb578eaba52ba2e36feb2e337c5ef6f58e36462db440ce06baf77311ae27a374fbdc1295320a9a1ea221cdac1ab2e71567bc84ba9fe910771e625c7f3b7edfe", 
        "role": "admin"
    },
    "researcher": {
        "password_hash": "scrypt:32768:8:1$XTUsqMq2Y1axdIp5$452bccce3d9b8935a4601c74686baa8f014e7247485dcc10319649ddb987a62dfc79027a3fdb16fd7b9959879524b48eab05a00e5ae8a2cf83e8600c828b7768", 
        "role": "researcher"
    }
}

SECRET_KEY = os.getenv("JWT_SECRET", "CHANGE_THIS_SECRET")


@login_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    user = USERS.get(username)
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode({
        "username": username,
        "role": user["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    }, SECRET_KEY, algorithm="HS256")

    return jsonify({
        "message": "Login successful",
        "token": token
    }), 200
