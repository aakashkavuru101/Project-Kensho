# kensho_engine/brain.py
import json
import spacy
import re

# Load the English NLP model from spaCy
# You must run 'python -m spacy download en_core_web_sm' first
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Spacy 'en_core_web_sm' model not found.")
    print("Please run 'python -m spacy download en_core_web_sm' to install it.")
    exit()

# Keywords to identify thematic group headings
THEME_KEYWORDS = ['phase', 'section', 'module', 'part', 'stage', 'step', 'area']
# Action verbs that typically signify a task
TASK_VERBS = [
    'create', 'develop', 'deploy', 'finalize', 'review', 'test', 'implement',
    'build', 'design', 'configure', 'prepare', 'submit', 'validate', 'verify'
]

def analyze_document_text(document_text: str, project_title: str = "Kensho Analyzed Project") -> dict:
    """
    Analyzes raw text using NLP to extract a structured project plan.
    This is the core "Brain" logic.
    """
    print("Analyzing document with NLP Brain...")
    doc = nlp(document_text)
    
    plan = {
        "project_name": project_title,
        "language": "EN",
        "thematic_groups": []
    }

    current_group = None

    # Iterate through sentences to find themes and tasks
    for sent in doc.sents:
        text = sent.text.strip().replace('\n', ' ')
        if not text:
            continue

        lower_text = text.lower()

        # Check if the sentence defines a new thematic group
        is_theme_heading = any(f'{keyword}:' in lower_text or f'{keyword} –' in lower_text for keyword in THEME_KEYWORDS)
        
        if is_theme_heading and len(text) < 100: # Assume headings are short
            if current_group:
                plan["thematic_groups"].append(current_group)
            
            current_group = {
                "group_name": text,
                "group_description": "",
                "tasks": []
            }
            continue

        # If we don't have a group yet, create a default one
        if not current_group:
            current_group = {
                "group_name": "General Requirements",
                "group_description": "Tasks identified in the document.",
                "tasks": []
            }

        # Check if the sentence describes a task
        root_verb = [token for token in sent if token.dep_ == "ROOT" and token.pos_ == "VERB"]
        is_task = any(verb.lemma_ in TASK_VERBS for verb in root_verb)

        if is_task:
            owner = None
            # Simple regex to find a potential owner (email)
            email_match = re.search(r'[\w\.-]+@[\w\.-]+', text)
            if email_match:
                owner = email_match.group(0)

            task = {
                "task_name": text,
                "details": f"Source sentence: '{text}'",
                "owner": owner
            }
            current_group["tasks"].append(task)

    # Add the last processed group to the plan
    if current_group and (not plan["thematic_groups"] or current_group["group_name"] != plan["thematic_groups"][-1]["group_name"]):
        plan["thematic_groups"].append(current_group)

    print("Analysis complete.")
    return plan
