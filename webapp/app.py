# webapp/app.py
from flask import Flask, render_template, request, jsonify
import os
import sys
import subprocess
import json

# Add the project root to the Python path to allow imports from kensho_engine
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kensho_engine.brain import analyze_document_text
from kensho_engine.utils import load_config

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

@app.route('/get_config_status', methods=['GET'])
def get_config_status():
    """
    Returns the configuration status for each service.
    Checks which services have their required configuration values filled out.
    """
    try:
        # Get the project root directory and config path
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        config_path = os.path.join(project_root, 'config.ini')
        
        # Load configuration
        config = load_config(config_path)
        if not config:
            # If config can't be loaded, assume all services are unconfigured
            return jsonify({
                'jira': False,
                'asana': False,
                'confluence': False,
                'trello': False,
                'slack': False,
                'github': False
            })
        
        status = {}
        
        # Check Jira configuration
        try:
            jira_section = config['jira']
            status['jira'] = (
                bool(jira_section.get('server', '').strip()) and
                bool(jira_section.get('email', '').strip()) and
                bool(jira_section.get('api_token', '').strip()) and
                bool(jira_section.get('project_key', '').strip())
            )
        except KeyError:
            status['jira'] = False
            
        # Check Asana configuration
        try:
            asana_section = config['asana']
            status['asana'] = (
                bool(asana_section.get('personal_access_token', '').strip()) and
                bool(asana_section.get('workspace_gid', '').strip())
            )
        except KeyError:
            status['asana'] = False
            
        # Check Confluence configuration
        try:
            confluence_section = config['confluence']
            status['confluence'] = (
                bool(confluence_section.get('url', '').strip()) and
                bool(confluence_section.get('email', '').strip()) and
                bool(confluence_section.get('api_token', '').strip()) and
                bool(confluence_section.get('space_key', '').strip())
            )
        except KeyError:
            status['confluence'] = False
            
        # Check Trello configuration
        try:
            trello_section = config['trello']
            status['trello'] = (
                bool(trello_section.get('api_key', '').strip()) and
                bool(trello_section.get('api_token', '').strip())
            )
        except KeyError:
            status['trello'] = False
            
        # Check Slack configuration
        try:
            slack_section = config['slack']
            status['slack'] = (
                bool(slack_section.get('bot_token', '').strip()) and
                bool(slack_section.get('channel_id', '').strip())
            )
        except KeyError:
            status['slack'] = False
            
        # Check GitHub configuration
        try:
            github_section = config['github']
            status['github'] = (
                bool(github_section.get('personal_access_token', '').strip()) and
                bool(github_section.get('repository', '').strip())
            )
        except KeyError:
            status['github'] = False
        
        return jsonify(status)
        
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
