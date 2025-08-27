# kensho_engine/hands.py
import argparse
import json
import logging
from kensho_engine.utils import load_config
from kensho_engine.connectors import jira_connector, asana_connector, confluence_connector, trello_connector, slack_connector, github_connector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    parser = argparse.ArgumentParser(description="Project Kensho 'Hands' - API Integration Orchestrator")
    parser.add_argument('--input', type=str, required=True, help='Path to the Kensho JSON output file.')
    parser.add_argument('--target', type=str, required=True, choices=['jira', 'asana', 'confluence', 'trello', 'slack', 'github'], help='Target platform.')
    parser.add_argument('--config', type=str, default='config.ini', help='Path to the configuration file.')
    args = parser.parse_args()

    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            plan_data = json.load(f)
    except FileNotFoundError:
        logging.error(f"Input file not found: {args.input}")
        return

    config = load_config(args.config)
    if not config:
        logging.error("Failed to load configuration. Exiting.")
        return

    logging.info(f"Initializing process for target: {args.target.upper()}")

    success = False
    if args.target == 'jira':
        success = jira_connector.create_project(plan_data, config)
    elif args.target == 'asana':
        success = asana_connector.create_project(plan_data, config)
    elif args.target == 'confluence':
        success = confluence_connector.create_project_documentation(plan_data, config)
    elif args.target == 'trello':
        success = trello_connector.create_board(plan_data, config)
    elif args.target == 'slack':
        success = slack_connector.post_summary(plan_data, config)
    elif args.target == 'github':
        success = github_connector.create_issues(plan_data, config)
    
    if success:
        logging.info(f"Process for target '{args.target}' completed successfully.")
    else:
        logging.error(f"Process for target '{args.target}' failed. Please check the logs.")

if __name__ == "__main__":
    main()
        