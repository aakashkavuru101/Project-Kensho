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
THEME_KEYWORDS = ["phase", "section", "module", "part", "stage", "step", "area", "group", "component", "feature", "deliverable"]
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
    "establish",
    "conduct",
    "ensure",
    "support",
    "deliver",
    "manage",
    "coordinate",
]

# Keywords to identify project managers and team members
ROLE_KEYWORDS = ["manager", "lead", "developer", "analyst", "coordinator", "owner", "responsible", "accountable"]
# Keywords to identify requirements
REQUIREMENT_KEYWORDS = ["must", "should", "shall", "required", "requirement", "needs to", "has to", "will", "expected to"]
# Keywords to identify dates and timelines
DATE_KEYWORDS = ["deadline", "due", "start", "end", "completion", "timeline", "schedule", "by"]
# Status keywords
STATUS_KEYWORDS = ["completed", "in progress", "pending", "planned", "not started", "active", "closed"]


def extract_project_metadata(doc, project_title: str) -> dict:
    """Extract comprehensive project metadata from the document."""
    metadata = {
        "projectName": project_title,
        "projectManager": "Not Specified",
        "projectObjective": "",
        "startDate": "",
        "dueDate": "",
        "projectStatus": "In Progress",
        "team": [],
        "phases": [],
        "requirements": []
    }
    
    # Extract project objective from first few sentences
    sentences = list(doc.sents)[:5]  # Look at first 5 sentences for objective
    for sent in sentences:
        text = sent.text.strip()
        if any(keyword in text.lower() for keyword in ["objective", "goal", "purpose", "aim", "deliver"]):
            metadata["projectObjective"] = text
            break
    
    # If no explicit objective found, generate one from project context
    if not metadata["projectObjective"]:
        metadata["projectObjective"] = f"To deliver a comprehensive solution for {project_title.lower()} with structured planning and execution."
    
    # Extract team members and roles
    team_members = []
    for sent in doc.sents:
        text = sent.text.strip()
        # Look for names with role indicators
        if any(role in text.lower() for role in ROLE_KEYWORDS):
            # Extract potential team member info
            for token in sent:
                if token.pos_ == "PERSON" or (token.ent_type_ == "PERSON"):
                    role = "Team Member"
                    for role_keyword in ROLE_KEYWORDS:
                        if role_keyword in text.lower():
                            role = role_keyword.title()
                            break
                    team_members.append({
                        "memberName": token.text,
                        "role": role,
                        "level": "Core Team"
                    })
    
    # Add default project manager if none found
    if not team_members:
        team_members.append({
            "memberName": "Project Manager",
            "role": "Project Management",
            "level": "Lead"
        })
    
    metadata["team"] = team_members
    return metadata


def extract_requirements(doc, source_name: str = "Document Analysis") -> list:
    """Extract and classify requirements from the document."""
    requirements = []
    req_id_counter = 1
    
    for sent in doc.sents:
        text = sent.text.strip()
        if not text:
            continue
            
        # Check if sentence contains requirement indicators
        is_requirement = any(keyword in text.lower() for keyword in REQUIREMENT_KEYWORDS)
        
        if is_requirement:
            # Determine requirement type
            req_type = "Functional"
            if any(keyword in text.lower() for keyword in ["performance", "security", "usability", "reliability", "scalability"]):
                req_type = "Non-Functional"
            
            requirements.append({
                "reqId": f"REQ-{req_id_counter:03d}",
                "type": req_type,
                "description": text,
                "source": source_name,
                "owner": "Not Specified",
                "status": "Confirmed"
            })
            req_id_counter += 1
    
    return requirements


def extract_phases_and_tasks(thematic_groups: list) -> list:
    """Convert thematic groups into structured phases with subtasks."""
    phases = []
    
    for i, group in enumerate(thematic_groups):
        phase = {
            "phaseName": group.get("group_name", f"Phase {i+1}"),
            "phaseOwner": "Not Specified", 
            "phaseStatus": "In Progress" if i == 0 else "Pending",
            "subTasks": []
        }
        
        # Convert tasks to subtasks
        for task in group.get("tasks", []):
            subtask = {
                "taskName": task.get("task_name", ""),
                "assignee": task.get("owner", "Development Team"),
                "status": "In Progress" if i == 0 else "Pending"
            }
            phase["subTasks"].append(subtask)
        
        phases.append(phase)
    
    return phases


def generate_professional_text_output(plan_data: dict) -> str:
    """Generate professional, insightful text output for project analysis."""
    output_lines = []
    
    # Header with mission
    output_lines.append(f"# {plan_data.get('projectName', 'Kensho Project Analysis')}")
    output_lines.append("")
    output_lines.append("## Project Analysis Summary")
    output_lines.append("")
    output_lines.append("Thank you for providing this document for analysis. Kensho has processed the content and identified key project components, requirements, and structural elements. This analysis transforms unstructured information into a comprehensive project blueprint.")
    output_lines.append("")
    
    # Project objective and insights
    if plan_data.get("projectObjective"):
        output_lines.append("### Project Objective")
        output_lines.append(f"**Objective:** {plan_data['projectObjective']}")
        output_lines.append("")
    
    # Thematic grouping insights
    thematic_groups = plan_data.get("thematic_groups", [])
    if thematic_groups:
        output_lines.append("### Thematic Grouping Analysis")
        output_lines.append("")
        output_lines.append("The document reveals several key thematic areas that naturally group the project deliverables:")
        output_lines.append("")
        
        for i, group in enumerate(thematic_groups, 1):
            group_name = group.get("group_name", f"Group {i}")
            tasks = group.get("tasks", [])
            output_lines.append(f"**{i}. {group_name}**")
            if group.get("group_description"):
                output_lines.append(f"   {group['group_description']}")
            output_lines.append(f"   • Contains {len(tasks)} identified deliverable(s)")
            if tasks:
                for task in tasks[:3]:  # Show first 3 tasks
                    output_lines.append(f"   • {task.get('task_name', '')}")
                if len(tasks) > 3:
                    output_lines.append(f"   • ... and {len(tasks) - 3} more items")
            output_lines.append("")
    
    # Requirements analysis
    requirements = plan_data.get("requirements", [])
    if requirements:
        functional_reqs = [r for r in requirements if r.get("type") == "Functional"]
        non_functional_reqs = [r for r in requirements if r.get("type") == "Non-Functional"]
        
        output_lines.append("### Requirements Analysis")
        output_lines.append("")
        output_lines.append(f"Kensho identified **{len(requirements)} total requirements** from the document:")
        output_lines.append(f"• **{len(functional_reqs)} Functional Requirements** - Core system capabilities")
        output_lines.append(f"• **{len(non_functional_reqs)} Non-Functional Requirements** - Quality and performance criteria")
        output_lines.append("")
        
        if functional_reqs:
            output_lines.append("#### Key Functional Requirements:")
            for req in functional_reqs[:5]:  # Show first 5
                output_lines.append(f"• **{req.get('reqId')}:** {req.get('description', '')}")
            if len(functional_reqs) > 5:
                output_lines.append(f"• ... and {len(functional_reqs) - 5} additional functional requirements")
            output_lines.append("")
    
    # Strategic recommendations
    output_lines.append("### Strategic Recommendations")
    output_lines.append("")
    output_lines.append("Based on this analysis, Kensho recommends the following approach:")
    output_lines.append("")
    output_lines.append("1. **Structured Execution:** Use the identified thematic groups as your project work streams")
    output_lines.append("2. **Requirements Traceability:** Each requirement has been assigned an ID for tracking throughout the project lifecycle")
    output_lines.append("3. **Stakeholder Alignment:** Review the extracted objectives and requirements with key stakeholders to ensure accuracy")
    output_lines.append("4. **Iterative Planning:** Use this structured output as a foundation for detailed project planning and estimation")
    output_lines.append("")
    
    # Footer
    output_lines.append("---")
    output_lines.append("")
    output_lines.append("*This analysis was generated by Project Kensho - bridging the gap between unstructured documents and structured project plans.*")
    
    return "\n".join(output_lines)


def analyze_document_text(document_text: str, project_title: str = "Kensho Analyzed Project") -> dict:
    """
    Analyzes raw text using NLP to extract a structured project plan.
    This is the core "Brain" logic with robust error handling and enhanced metadata extraction.

    Args:
        document_text: Raw text content to analyze
        project_title: Title for the project plan

    Returns:
        dict: Comprehensive structured project plan

    Raises:
        ValueError: If document_text is empty or invalid
        RuntimeError: If NLP processing fails
    """
    if not document_text or not document_text.strip():
        logger.error("Empty or invalid document text provided")
        raise ValueError("Document text cannot be empty")

    logger.info(f"Starting enhanced document analysis for project: {project_title}")
    logger.info(f"Document length: {len(document_text)} characters")

    try:
        # Preprocess the document text to improve sentence segmentation
        preprocessed_text = document_text.replace('\n-', '\n•').replace('\n•', '.\n•')
        preprocessed_text = preprocessed_text.replace('\n\n', '.\n\n')
        
        # Process text with spaCy - this could fail if text is too large or contains invalid characters
        doc = nlp(preprocessed_text)
        logger.info(f"Successfully processed document with {len(list(doc.sents))} sentences")
    except Exception as e:
        logger.error(f"Failed to process document with spaCy: {e}")
        raise RuntimeError(f"NLP processing failed: {e}")

    # Start with enhanced project metadata
    plan = extract_project_metadata(doc, project_title)
    
    # Keep the original thematic groups structure for backward compatibility
    plan["language"] = "EN"
    plan["thematic_groups"] = []

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

                # Check if the sentence defines a new thematic group (enhanced detection)
                is_theme_heading = (
                    any(f"{keyword}:" in lower_text or f"{keyword} –" in lower_text for keyword in THEME_KEYWORDS) or
                    re.match(r'^(phase|section|module|part|stage|step)\s+\d+', lower_text) or
                    (text.startswith("Phase ") and ":" in text) or
                    (len(text.split()) <= 6 and any(keyword in lower_text for keyword in THEME_KEYWORDS))
                )

                if is_theme_heading and len(text) < 150:  # Increased threshold for longer headings
                    if current_group:
                        plan["thematic_groups"].append(current_group)

                    current_group = {"group_name": text, "group_description": "", "tasks": []}
                    groups_found += 1
                    logger.debug(f"Found thematic group: {text}")
                    continue

                # If we don't have a group yet, create a default one
                if not current_group:
                    current_group = {
                        "group_name": "Core Requirements",
                        "group_description": "Primary deliverables and tasks identified in the document.",
                        "tasks": [],
                    }

                # Check if the sentence describes a task - with error handling
                try:
                    root_verb = [token for token in sent if token.dep_ == "ROOT" and token.pos_ == "VERB"]
                    is_task = any(verb.lemma_ in TASK_VERBS for verb in root_verb)
                    
                    # Also check for bullet points and numbered lists
                    if not is_task:
                        is_task = (text.startswith("-") or text.startswith("•") or 
                                 re.match(r'^\d+\.', text) or text.startswith("*"))
                except Exception as e:
                    logger.warning(f"Error processing sentence {sent_idx} for task detection: {e}")
                    is_task = False

                if is_task:
                    owner = None
                    # Enhanced owner extraction
                    try:
                        # Look for email addresses
                        email_match = re.search(r"[\w\.-]+@[\w\.-]+", text)
                        if email_match:
                            owner = email_match.group(0)
                        else:
                            # Look for role assignments
                            for role in ROLE_KEYWORDS:
                                if role in lower_text:
                                    owner = role.title()
                                    break
                        
                        logger.debug(f"Found task owner: {owner}")
                    except Exception as e:
                        logger.warning(f"Error extracting owner from text: {e}")

                    task = {
                        "task_name": text,
                        "details": f"Extracted from: '{text[:100]}{'...' if len(text) > 100 else ''}'",
                        "owner": owner or "Development Team"
                    }
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

        # Extract requirements and convert thematic groups to phases
        plan["requirements"] = extract_requirements(doc, f"{project_title} Analysis")
        plan["phases"] = extract_phases_and_tasks(plan["thematic_groups"])
        
        # Generate professional text output
        plan["professional_analysis"] = generate_professional_text_output(plan)

    except Exception as e:
        logger.error(f"Critical error during document analysis: {e}")
        raise RuntimeError(f"Analysis failed: {e}")

    logger.info(f"Enhanced analysis complete. Found {groups_found} groups, {tasks_found} tasks, and {len(plan.get('requirements', []))} requirements")
    return plan
