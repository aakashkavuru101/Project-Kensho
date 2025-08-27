# kensho_engine/brain.py
import logging
import re

import spacy

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load the English NLP model from spaCy
# You must run 'python -m spacy download en_core_web_sm' first
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("Successfully loaded spaCy English model")
except OSError as e:
    logger.error("Spacy 'en_core_web_sm' model not found.")
    logger.error("Please run 'python -m spacy download en_core_web_sm' to install it.")
    logger.error(f"Error details: {e}")
    exit(1)

# Keywords to identify thematic group headings
THEME_KEYWORDS = ["phase", "section", "module", "part", "stage", "step", "area"]
# Action verbs that typically signify a task
TASK_VERBS = [
    "create",
    "develop",
    "deploy",
    "finalize",
    "review",
    "test",
    "implement",
    "build",
    "design",
    "configure",
    "prepare",
    "submit",
    "validate",
    "verify",
]


def analyze_document_text(document_text: str, project_title: str = "Kensho Analyzed Project") -> dict:
    """
    Analyzes raw text using NLP to extract a structured project plan.
    This is the core "Brain" logic with robust error handling.

    Args:
        document_text: Raw text content to analyze
        project_title: Title for the project plan

    Returns:
        dict: Structured project plan

    Raises:
        ValueError: If document_text is empty or invalid
        RuntimeError: If NLP processing fails
    """
    if not document_text or not document_text.strip():
        logger.error("Empty or invalid document text provided")
        raise ValueError("Document text cannot be empty")

    logger.info(f"Starting document analysis for project: {project_title}")
    logger.info(f"Document length: {len(document_text)} characters")

    try:
        # Process text with spaCy - this could fail if text is too large or contains invalid characters
        doc = nlp(document_text)
        logger.info(f"Successfully processed document with {len(list(doc.sents))} sentences")
    except Exception as e:
        logger.error(f"Failed to process document with spaCy: {e}")
        raise RuntimeError(f"NLP processing failed: {e}")

    plan = {"project_name": project_title, "language": "EN", "thematic_groups": []}

    current_group = None
    tasks_found = 0
    groups_found = 0

    try:
        # Iterate through sentences to find themes and tasks
        for sent_idx, sent in enumerate(doc.sents):
            try:
                text = sent.text.strip().replace("\n", " ")
                if not text:
                    continue

                lower_text = text.lower()

                # Check if the sentence defines a new thematic group
                is_theme_heading = any(
                    f"{keyword}:" in lower_text or f"{keyword} –" in lower_text for keyword in THEME_KEYWORDS
                )

                if is_theme_heading and len(text) < 100:  # Assume headings are short
                    if current_group:
                        plan["thematic_groups"].append(current_group)

                    current_group = {"group_name": text, "group_description": "", "tasks": []}
                    groups_found += 1
                    logger.debug(f"Found thematic group: {text}")
                    continue

                # If we don't have a group yet, create a default one
                if not current_group:
                    current_group = {
                        "group_name": "General Requirements",
                        "group_description": "Tasks identified in the document.",
                        "tasks": [],
                    }

                # Check if the sentence describes a task - with error handling
                try:
                    root_verb = [token for token in sent if token.dep_ == "ROOT" and token.pos_ == "VERB"]
                    is_task = any(verb.lemma_ in TASK_VERBS for verb in root_verb)
                except Exception as e:
                    logger.warning(f"Error processing sentence {sent_idx} for task detection: {e}")
                    is_task = False

                if is_task:
                    owner = None
                    # Simple regex to find a potential owner (email) - with error handling
                    try:
                        email_match = re.search(r"[\w\.-]+@[\w\.-]+", text)
                        if email_match:
                            owner = email_match.group(0)
                            logger.debug(f"Found task owner: {owner}")
                    except Exception as e:
                        logger.warning(f"Error extracting email from text: {e}")

                    task = {"task_name": text, "details": f"Source sentence: '{text}'", "owner": owner}
                    current_group["tasks"].append(task)
                    tasks_found += 1
                    logger.debug(f"Found task: {text[:50]}...")

            except Exception as e:
                logger.warning(f"Error processing sentence {sent_idx}: {e}")
                continue

        # Add the last processed group to the plan
        if current_group and (
            not plan["thematic_groups"] or current_group["group_name"] != plan["thematic_groups"][-1]["group_name"]
        ):
            plan["thematic_groups"].append(current_group)

    except Exception as e:
        logger.error(f"Critical error during document analysis: {e}")
        raise RuntimeError(f"Analysis failed: {e}")

    logger.info(f"Analysis complete. Found {groups_found} groups and {tasks_found} tasks")
    return plan
