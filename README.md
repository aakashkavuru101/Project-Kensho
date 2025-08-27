**Project Kensho: Intelligent Project Plan Automation**

_Project Kensho is a powerful automation engine that transforms unstructured documents into structured, actionable project plans. It reads contracts, project briefs, or statements of work and uses Natural Language Processing (NLP) to automatically generate tasks, epics, and pages in your favorite project management tools._

The Problem
In any project, the initial setup is a major bottleneck. Manually reading through long documents, identifying key deliverables, and creating dozens of tickets in Jira or Asana is a tedious, error-prone process that consumes valuable time. This manual data entry is a low-value task that slows down the kick-off of any new initiative.

The Solution
Project Kensho eliminates this manual work. It acts as an intelligent agent that automates the entire workflow, bridging the gap between a document and a fully populated project plan. By parsing the text and integrating directly with project management APIs, Kensho allows teams to go from contract to a ready-to-work project plan in minutes, not hours.

Key Features
🤖 NLP-Powered "Brain": Utilizes spaCy for advanced NLP to intelligently parse documents, identify thematic sections, and extract actionable tasks based on linguistic patterns.

🔌 Multi-Platform "Hands": A suite of robust API connectors to push the generated plan to the most popular corporate platforms:

Jira: Creates Epics and Stories.

Asana: Creates Projects, Sections, and Tasks.

Confluence: Generates a structured documentation hierarchy.

Trello: Builds a complete board with lists and cards.

Slack: Posts a formatted summary for team notifications.

💻 Interactive Web UI: A clean, modern web application built with Flask and Tailwind CSS allows for easy, interactive use. Simply upload a document and execute the plan with the click of a button.

⚙️ Decoupled Core Engine: The entire backend logic is packaged as a reusable Python library (kensho_engine), completely separate from the web interface, allowing for easy integration into other scripts or automated workflows.

** CLI for Automation:** Includes a command-line interface for power users and CI/CD pipeline integration.

How It Works: The "Brain and Hands" Model
Kensho operates on a simple but powerful architectural principle:

The Brain (kensho_engine/brain.py): The user provides a text document. The Brain analyzes this text, creating a standardized JSON "blueprint" of the project plan.

The Hands (kensho_engine/hands.py & connectors/): This blueprint is passed to the Hands, which connect to the chosen platform's API and execute the plan, creating all the necessary artifacts.

graph TD
    A[Unstructured Document] --> B{Kensho Brain (NLP Analysis)};
    B -- Creates --> C[Structured Plan (JSON Blueprint)];
    C --> D{Kensho Hands (API Connectors)};
    D --> E[Jira, Asana, Confluence, etc.];

Technology Stack
Backend: Python, Flask

NLP: spaCy

Frontend: HTML, Tailwind CSS, Vanilla JavaScript

API Connectors: jira-python, asana, atlassian-python-api, py-trello, slack_sdk

Getting Started
1. Installation
First, clone the repository and set up the environment. Full, detailed instructions are in the installation guide.

# Clone the repository
git clone <your-repository-url>
cd project_kensho

# Follow the setup guide
# (See INSTALL.md for details on virtual environment and dependencies)

👉 See the full INSTALL.md for complete setup instructions.

2. Configuration
Before running, you must provide your API credentials.

Rename config.ini.template to config.ini.

Open config.ini and fill in the required keys and tokens for the services you wish to use.

3. Running the Application
The easiest way to use Kensho is through the web interface.

# Start the web server from the root directory
python webapp/app.py

# Open your browser and navigate to http://127.0.0.1:5001

👉 See the GUIDE.md for detailed usage instructions, including the command-line interface.

Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue for any bugs or feature requests.
