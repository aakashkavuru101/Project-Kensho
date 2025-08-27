# webapp/app.py
from flask import Flask, render_template, request, jsonify
import os
import sys
import subprocess
import json

# Add the project root to the Python path to allow imports from kensho_engine
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kensho_engine.brain import analyze_document_text

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Handles file upload, calls the Brain to analyze it,
    and returns the structured JSON.
    """
    if 'document' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['document']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        try:
            content = file.read().decode('utf-8')
            project_title = os.path.splitext(file.filename)[0].replace('_', ' ').title()
            
            # Call the real Brain logic
            plan_data = analyze_document_text(content, project_title)
            return jsonify(plan_data)

        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/execute', methods=['POST'])
def execute():
    """
    Receives the plan JSON and a target platform,
    then calls the Hands orchestrator.
    """
    data = request.json
    plan_data = data.get('plan')
    target = data.get('target')

    if not plan_data or not target:
        return jsonify({"error": "Missing plan data or target"}), 400

    json_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_plan.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(plan_data, f, ensure_ascii=False, indent=4)

    try:
        # Get the project root directory
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        # Construct the command to run the hands orchestrator as a module
        command = [
            sys.executable, '-m', 'kensho_engine.hands',
            '--input', json_path,
            '--target', target,
            '--config', os.path.join(project_root, 'config.ini')
        ]
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            cwd=project_root # Run from the project root
        )
        
        return jsonify({
            "success": True,
            "message": f"Successfully executed for target: {target}",
            "logs": result.stdout
        })

    except subprocess.CalledProcessError as e:
        return jsonify({
            "success": False,
            "error": f"Execution failed for target: {target}",
            "logs": f"STDOUT:\n{e.stdout}\n\nSTDERR:\n{e.stderr}"
        }), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
