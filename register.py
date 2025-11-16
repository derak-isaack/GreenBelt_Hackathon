# login.py
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
import jwt
import datetime
import os

login_bp = Blueprint('login', __name__)

USERS = {
    "admin": {
        "password_hash": "pbkdf2:sha256:260000$KfKuPp6l9asdd$bd3ds..." ,  
        "role": "admin"
    },
    "researcher": {
        "password_hash": "pbkdf2:sha256:260000$bbfHPPssa...$7204af2...", 
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
