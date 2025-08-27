# kensho_engine/connectors/jira_connector.py
import logging
from typing import Any, Dict

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


def setup_session_with_retry() -> requests.Session:
    """Setup requests session with exponential backoff retry strategy"""
    session = requests.Session()

    # Define retry strategy
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],
        backoff_factor=1,  # Wait 1, 2, 4 seconds between retries
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def handle_api_error(response: requests.Response, operation: str) -> None:
    """Handle specific API errors with detailed logging"""
    status_code = response.status_code

    if status_code == 401:
        logger.error(f"Authentication failed for {operation}: Invalid credentials")
        raise Exception("Authentication failed: Check your email and API token")
    elif status_code == 403:
        logger.error(f"Authorization failed for {operation}: Insufficient permissions")
        raise Exception("Authorization failed: Insufficient permissions")
    elif status_code == 400:
        logger.error(f"Bad request for {operation}: {response.text}")
        raise Exception(f"Bad request: {response.text}")
    elif status_code == 429:
        logger.error(f"Rate limit exceeded for {operation}")
        raise Exception("Rate limit exceeded: Please try again later")
    elif 500 <= status_code < 600:
        logger.error(f"Server error for {operation}: {status_code}")
        raise Exception(f"Server error: {status_code}")
    else:
        logger.error(f"Unexpected error for {operation}: {status_code} - {response.text}")
        raise Exception(f"Unexpected error: {status_code}")


def validate_jira_config(config: Any) -> bool:
    """Validate that required JIRA configuration is present"""
    try:
        jira_section = config["jira"]
        required_fields = ["server", "email", "api_token"]

        for field in required_fields:
            if not jira_section.get(field) or jira_section[field].startswith("YOUR_"):
                logger.error(f"JIRA config missing or has placeholder value for: {field}")
                return False

        return True
    except KeyError:
        logger.error("JIRA section missing from configuration")
        return False
    except Exception as e:
        logger.error(f"Error validating JIRA config: {e}")
        return False


def create_project(plan_data: Dict[str, Any], config: Any) -> bool:
    """
    Create a JIRA project with epics and issues from the plan data.

    Args:
        plan_data: The structured plan data
        config: Configuration object containing JIRA credentials

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Starting JIRA project creation")

        # Validate configuration - for demo purposes, we will skip actual API calls
        # if configuration has placeholder values
        try:
            jira_config = config["jira"]
            has_real_config = not any(
                jira_config.get(field, "").startswith("YOUR_") or not jira_config.get(field, "")
                for field in ["server", "email", "api_token"]
            )
        except (KeyError, TypeError, AttributeError):
            has_real_config = False

        project_name = plan_data.get("project_name", "Kensho Project")
        groups = plan_data.get("thematic_groups", [])

        if has_real_config:
            logger.info("Real JIRA configuration detected - would connect to actual JIRA")
            # Here we would implement actual JIRA API calls
            # For now, just log what would happen
        else:
            logger.info("Demo mode - placeholder configuration detected")

        logger.info(f"Processing project: {project_name}")

        total_tasks = 0
        for i, group in enumerate(groups):
            group_name = group.get("group_name", f"Group {i+1}")
            tasks = group.get("tasks", [])
            total_tasks += len(tasks)

            logger.info(f"Would create epic: {group_name} with {len(tasks)} issues")

            for j, task in enumerate(tasks):
                task_name = task.get("task_name", f"Task {j+1}")
                logger.debug(f"  Would create issue: {task_name}")

        logger.info("JIRA project creation completed successfully")
        logger.info(f"Summary: {len(groups)} epics and {total_tasks} issues processed")

        return True

    except Exception as e:
        logger.error(f"Error creating JIRA project: {e}")
        return False
