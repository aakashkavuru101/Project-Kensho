# kensho_engine/hands.py
import argparse
import json
import logging
import os
import sys
from datetime import datetime

from Kensho_engine.connectors import (
    asana_connector,
    confluence_connector,
    jira_connector,
    slack_connector,
    trello_connector,
)
from Kensho_engine.utils import load_config


# Setup structured logging
def setup_logging():
    """Setup structured logging with both console and file output"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create formatters
    detailed_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(detailed_formatter)

    # File handler - create logs directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'kensho_{datetime.now().strftime("%Y%m%d")}.log')

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = setup_logging()


def validate_plan_data(plan_data: dict) -> bool:
    """
    Validate that plan_data contains required fields before API calls.

    Args:
        plan_data: The plan data dictionary to validate

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        if not isinstance(plan_data, dict):
            logger.error("plan_data is not a dictionary")
            return False

        required_fields = ["project_name", "thematic_groups"]
        for field in required_fields:
            if field not in plan_data:
                logger.error(f"Missing required field: {field}")
                return False

        if not isinstance(plan_data["thematic_groups"], list):
            logger.error("thematic_groups is not a list")
            return False

        # Validate each group has required fields
        for i, group in enumerate(plan_data["thematic_groups"]):
            if not isinstance(group, dict):
                logger.error(f"Group {i} is not a dictionary")
                return False
            if "group_name" not in group or "tasks" not in group:
                logger.error(f"Group {i} missing required fields")
                return False
            if not isinstance(group["tasks"], list):
                logger.error(f"Group {i} tasks is not a list")
                return False

        logger.info("Plan data validation successful")
        return True

    except Exception as e:
        logger.error(f"Error validating plan data: {e}")
        return False


def main():
    """Main function with comprehensive error handling and proper exit codes"""
    try:
        parser = argparse.ArgumentParser(description="Project Kensho 'Hands' - API Integration Orchestrator")
        parser.add_argument("--input", type=str, required=True, help="Path to the Kensho JSON output file.")
        parser.add_argument(
            "--target",
            type=str,
            required=True,
            choices=["jira", "asana", "confluence", "trello", "slack"],
            help="Target platform.",
        )
        parser.add_argument("--config", type=str, default="config.ini", help="Path to the configuration file.")
        args = parser.parse_args()

        logger.info("Starting Kensho Hands orchestrator")
        logger.info(f"Input file: {args.input}")
        logger.info(f"Target platform: {args.target}")
        logger.info(f"Config file: {args.config}")

        # Validate input file exists
        if not os.path.exists(args.input):
            logger.error(f"Input file not found: {args.input}")
            sys.exit(1)

        # Load and validate plan data
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                plan_data = json.load(f)
            logger.info("Successfully loaded plan data")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in input file: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error reading input file: {e}")
            sys.exit(1)

        # Validate plan data structure
        if not validate_plan_data(plan_data):
            logger.error("Plan data validation failed")
            sys.exit(1)

        # Load configuration
        config = load_config(args.config)
        if not config:
            logger.error("Failed to load configuration")
            sys.exit(1)
        logger.info("Configuration loaded successfully")

        logger.info(f"Initializing process for target: {args.target.upper()}")

        success = False
        try:
            if args.target == "jira":
                success = jira_connector.create_project(plan_data, config)
            elif args.target == "asana":
                success = asana_connector.create_project(plan_data, config)
            elif args.target == "confluence":
                success = confluence_connector.create_project_documentation(plan_data, config)
            elif args.target == "trello":
                success = trello_connector.create_board(plan_data, config)
            elif args.target == "slack":
                success = slack_connector.post_summary(plan_data, config)
        except Exception as e:
            logger.error(f"Unexpected error during {args.target} execution: {e}")
            success = False

        if success:
            logger.info(f"Process for target '{args.target}' completed successfully")
            sys.exit(0)
        else:
            logger.error(f"Process for target '{args.target}' failed")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
