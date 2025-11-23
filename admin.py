from flask import Blueprint, request, jsonify
import os
import jwt
import json
import datetime
from werkzeug.utils import secure_filename
import uuid

admin_bp = Blueprint("admin", __name__)

SECRET_KEY = os.getenv("JWT_SECRET", "CHANGE_THIS_SECRET")
UPLOAD_FOLDER = "public/uploads"
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_user_role():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header or " " not in auth_header:
        return None
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("role")
    except:
        return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route("/upload", methods=["POST"])
def upload_file():
    role = get_user_role()
    if role != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed. Only PDF, DOC, DOCX are permitted"}), 400

    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    if file_size > MAX_FILE_SIZE:
        return jsonify({"error": "File too large. Maximum size is 10MB"}), 400

    filename = secure_filename(file.filename)
    # Add timestamp to avoid conflicts
    name, ext = os.path.splitext(filename)
    unique_filename = f"{name}_{int(datetime.datetime.utcnow().timestamp())}{ext}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

    try:
        file.save(file_path)

        # Store metadata
        metadata = {
            "id": str(uuid.uuid4()),
            "original_filename": filename,
            "stored_filename": unique_filename,
            "file_path": file_path,
            "file_size": file_size,
            "upload_date": datetime.datetime.utcnow().isoformat(),
            "uploaded_by": "admin"  # Could get from token if needed
        }

        # Save metadata to a JSON file
        metadata_file = os.path.join(UPLOAD_FOLDER, "uploads_metadata.json")
        if os.path.exists(metadata_file):
            with open(metadata_file, "r") as f:
                uploads = json.load(f)
        else:
            uploads = []

        uploads.append(metadata)

        with open(metadata_file, "w") as f:
            json.dump(uploads, f, indent=4)

        return jsonify({
            "message": "File uploaded successfully",
            "file_id": metadata["id"],
            "filename": unique_filename
        }), 200

    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

@admin_bp.route("/uploads", methods=["GET"])
def get_uploads():
    role = get_user_role()
    if role != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    metadata_file = os.path.join(UPLOAD_FOLDER, "uploads_metadata.json")
    if not os.path.exists(metadata_file):
        return jsonify([]), 200

    with open(metadata_file, "r") as f:
        uploads = json.load(f)

    return jsonify(uploads), 200