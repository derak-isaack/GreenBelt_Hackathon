# research.py
from flask import Blueprint, request, jsonify
import jwt
import os
from functools import wraps
from summary import run_web_summary

research_bp = Blueprint('research', __name__)

SECRET_KEY = os.getenv("JWT_SECRET", "CHANGE_THIS_SECRET")


# -----------------------
#   JWT AUTH DECORATOR
# -----------------------
def token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = None

        # token expected as Authorization: Bearer <token>
        auth_header = request.headers.get("Authorization", None)
        if auth_header and " " in auth_header:
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Token missing"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user = data  # store user payload
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return fn(*args, **kwargs)
    return wrapper


# -------------------------
#   IN-MEMORY RESOURCE STORE
# -------------------------
# replace with DB / Supabase / Mongo later
RESOURCES = []


# -------------------------
#   LIST RESEARCH MATERIALS
# -------------------------
@research_bp.route("/resources", methods=["GET"])
@token_required
def list_resources():
    return jsonify({"resources": RESOURCES}), 200

@research_bp.route("/resources", methods=["POST"])
@token_required
def add_resource():
    role = request.user.get("role")

    if role != "admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    title = data.get("title")
    content = data.get("content")      
    source = data.get("source")        

    if not title or not content:
        return jsonify({"error": "Missing title or content"}), 400

    resource = {
        "id": len(RESOURCES) + 1,
        "title": title,
        "content": content,
        "source": source,
        "created_by": request.user.get("username"),
    }

    RESOURCES.append(resource)

    return jsonify({"message": "Resource added", "resource": resource}), 201


@research_bp.route("/summarize_article", methods=["POST"])
@token_required
def summarize_article():
    data = request.get_json()
    url = data.get("url", "")

    if not url:
        return jsonify({"error": "Missing article URL"}), 400

    summary = run_web_summary(url)

    return jsonify({"summary": summary}), 200
