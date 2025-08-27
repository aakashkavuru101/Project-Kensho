User Guide for Project Kensho
Project Kensho can be run in two ways: via the command line (for automation) or through the web interface (for interactive use).

Option 1: Using the Web Interface (Recommended)
This is the easiest way to use Project Kensho.

Start the Web Server:
From the root project_kensho directory, run the following command:

python webapp/app.py

Open Your Browser:
Navigate to http://127.0.0.1:5001 in your web browser.

Step 1: Analyze Document:

Click "Choose File" and select a plain text (.txt) file containing your project brief.

Click the "Analyze Document" button.

Step 2: Review and Execute:

The analyzed plan will appear in the JSON output box.

Click any of the "Send to..." buttons (e.g., "Send to Jira") to execute the "Hands" and push the plan to that platform.

A success or error message will appear.

Option 2: Using the Command Line
This method is ideal for scripting and automation.

Step 1: Run the "Brain" (Optional):
While the web app does this automatically, you can manually run the brain. You would need to modify brain/core_logic.py to read a file and call generate_json_from_text() to create an output_plan.json.

Step 2: Run the "Hands":
Use the hands/main.py orchestrator with a generated JSON file.

# Example: Push a plan to Trello
python hands/main.py --input output_plan.json --target trello
