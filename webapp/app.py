# webapp/app.py
import json
import logging
import os
import subprocess
import sys
import threading
import uuid
from datetime import datetime
from typing import Any, Dict

# Add the project root to the Python path to allow imports from kensho_engine
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, jsonify, render_template, request  # noqa: E402

from Kensho_engine.brain import analyze_document_text  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Store for async task status
task_status: Dict[str, Dict[str, Any]] = {}
task_lock = threading.Lock()

# Allowed file extensions and MIME types for security
ALLOWED_EXTENSIONS = {"txt"}
ALLOWED_MIME_TYPES = {"text/plain"}


def allowed_file(filename: str, mimetype: str) -> bool:
    """Check if uploaded file is allowed based on extension and MIME type"""
    if not filename:
        return False

    # Check file extension
    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        return False

    # Check MIME type
    if mimetype not in ALLOWED_MIME_TYPES:
        return False

    return True


def validate_file_content(content: str) -> bool:
    """Validate file content for security"""
    if not content or not content.strip():
        return False

    # Check file size (additional check)
    if len(content.encode("utf-8")) > 1024 * 1024:  # 1MB max content
        return False

    # Basic content validation - ensure it's readable text
    try:
        content.encode("utf-8")
        return True
    except UnicodeError:
        return False


@app.route("/")
def index():
    """Renders the main page."""
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Handles file upload, calls the Brain to analyze it,
    and returns the structured JSON with enhanced security.
    """
    logger.info("Received analysis request")

    if "document" not in request.files:
        logger.warning("No file part in request")
        return jsonify({"error": "No file part"}), 400

    file = request.files["document"]
    if file.filename == "":
        logger.warning("No file selected")
        return jsonify({"error": "No selected file"}), 400

    # Security validation
    if not allowed_file(file.filename, file.mimetype):
        logger.warning(f"Invalid file type: {file.filename}, MIME: {file.mimetype}")
        return jsonify({"error": "Only .txt files are allowed"}), 400

    try:
        content = file.read().decode("utf-8")

        # Validate content
        if not validate_file_content(content):
            logger.warning("Invalid file content")
            return jsonify({"error": "Invalid file content"}), 400

        project_title = os.path.splitext(file.filename)[0].replace("_", " ").title()

        logger.info(f"Analyzing document: {project_title}")

        # Call the real Brain logic with enhanced error handling
        plan_data = analyze_document_text(content, project_title)

        logger.info("Document analysis completed successfully")
        return jsonify(plan_data)

    except UnicodeDecodeError:
        logger.error("File encoding error")
        return jsonify({"error": "File must be UTF-8 encoded text"}), 400
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


def execute_hands_async(task_id: str, plan_data: Dict[str, Any], target: str, json_path: str):
    """Execute hands orchestrator asynchronously"""
    with task_lock:
        task_status[task_id]["status"] = "running"
        task_status[task_id]["message"] = "Execution in progress..."

    try:
        # Get the project root directory
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        # Construct the command to run the hands orchestrator as a module
        # Use absolute paths and validate input
        command = [
            sys.executable,
            "-m",
            "Kensho_engine.hands",
            "--input",
            os.path.abspath(json_path),
            "--target",
            target,
            "--config",
            os.path.abspath(os.path.join(project_root, "config.ini")),
        ]

        logger.info(f"Executing command for task {task_id}: {' '.join(command)}")

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            cwd=project_root,  # Run from the project root
            timeout=300,  # 5 minute timeout
        )

        with task_lock:
            task_status[task_id]["status"] = "completed"
            task_status[task_id]["success"] = True
            task_status[task_id]["message"] = f"Successfully executed for target: {target}"
            task_status[task_id]["logs"] = result.stdout
            task_status[task_id]["completed_at"] = datetime.now().isoformat()

        logger.info(f"Task {task_id} completed successfully")

    except subprocess.TimeoutExpired:
        with task_lock:
            task_status[task_id]["status"] = "failed"
            task_status[task_id]["success"] = False
            task_status[task_id]["message"] = f"Execution timed out for target: {target}"
            task_status[task_id]["completed_at"] = datetime.now().isoformat()
        logger.error(f"Task {task_id} timed out")

    except subprocess.CalledProcessError as e:
        with task_lock:
            task_status[task_id]["status"] = "failed"
            task_status[task_id]["success"] = False
            task_status[task_id]["message"] = f"Execution failed for target: {target}"
            task_status[task_id]["logs"] = f"STDOUT:\n{e.stdout}\n\nSTDERR:\n{e.stderr}"
            task_status[task_id]["completed_at"] = datetime.now().isoformat()
        logger.error(f"Task {task_id} failed with exit code {e.returncode}")

    except Exception as e:
        with task_lock:
            task_status[task_id]["status"] = "failed"
            task_status[task_id]["success"] = False
            task_status[task_id]["message"] = f"Unexpected error: {str(e)}"
            task_status[task_id]["completed_at"] = datetime.now().isoformat()
        logger.error(f"Task {task_id} failed with unexpected error: {e}")


@app.route("/execute", methods=["POST"])
def execute():
    """
    Receives the plan JSON and a target platform,
    then calls the Hands orchestrator asynchronously.
    """
    logger.info("Received execution request")

    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        plan_data = data.get("plan")
        target = data.get("target")

        if not plan_data or not target:
            logger.warning("Missing plan data or target")
            return jsonify({"error": "Missing plan data or target"}), 400

        # Validate target
        valid_targets = ["jira", "asana", "confluence", "trello", "slack"]
        if target not in valid_targets:
            logger.warning(f"Invalid target: {target}")
            return jsonify({"error": f"Invalid target. Must be one of: {valid_targets}"}), 400

        # Generate unique task ID
        task_id = str(uuid.uuid4())

        # Save plan data to temporary file with unique name
        json_filename = f"temp_plan_{task_id}.json"
        json_path = os.path.join(app.config["UPLOAD_FOLDER"], json_filename)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(plan_data, f, ensure_ascii=False, indent=4)

        # Initialize task status
        with task_lock:
            task_status[task_id] = {
                "status": "pending",
                "target": target,
                "created_at": datetime.now().isoformat(),
                "message": "Task queued for execution",
            }

        # Start async execution
        thread = threading.Thread(target=execute_hands_async, args=(task_id, plan_data, target, json_path))
        thread.daemon = True
        thread.start()

        logger.info(f"Started async execution for task {task_id}, target: {target}")

        return jsonify({"task_id": task_id, "status": "pending", "message": "Task queued for execution"})

    except Exception as e:
        logger.error(f"Error in execute endpoint: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/status/<task_id>", methods=["GET"])
def get_task_status(task_id: str):
    """Get the status of an async task"""
    with task_lock:
        if task_id not in task_status:
            return jsonify({"error": "Task not found"}), 404

        status = task_status[task_id].copy()

    return jsonify(status)


if __name__ == "__main__":
    # Production configuration
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_ENV") != "production"
    host = "0.0.0.0" if not debug else "127.0.0.1"

    logger.info(f"Starting Flask app on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)
