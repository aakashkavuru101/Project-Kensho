# kensho_engine/connectors/github_connector.py
import logging
import requests
import json

def create_issues(plan_data: dict, config) -> bool:
    """
    Creates GitHub issues for each task in the plan data.
    
    Args:
        plan_data (dict): The structured plan data from the Brain
        config: ConfigParser instance with GitHub configuration
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read GitHub configuration
        github_section = config['github']
        personal_access_token = github_section.get('personal_access_token', '').strip()
        repository = github_section.get('repository', '').strip()
        
        if not personal_access_token:
            logging.error("GitHub Personal Access Token not configured")
            return False
            
        if not repository:
            logging.error("GitHub repository not configured")
            return False
            
        # Validate repository format (user/repo)
        if '/' not in repository:
            logging.error(f"Invalid repository format: {repository}. Expected format: user/repo")
            return False
            
        # Set up headers for GitHub API
        headers = {
            'Authorization': f'token {personal_access_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        # GitHub API URL for creating issues
        api_url = f"https://api.github.com/repos/{repository}/issues"
        
        project_title = plan_data.get('project_title', 'Kensho Project')
        logging.info(f"Creating GitHub issues for project: {project_title}")
        
        total_issues_created = 0
        
        # Create issues for each thematic group and their tasks
        for group in plan_data.get('thematic_groups', []):
            group_name = group.get('group_name', 'Unknown Group')
            group_description = group.get('group_description', '')
            tasks = group.get('tasks', [])
            
            # Create a group-level issue if there are tasks
            if tasks:
                group_issue_body = f"**Project:** {project_title}\n\n"
                if group_description:
                    group_issue_body += f"**Description:** {group_description}\n\n"
                
                group_issue_body += "**Tasks in this group:**\n"
                for i, task in enumerate(tasks, 1):
                    task_name = task.get('task_name', f'Task {i}')
                    group_issue_body += f"{i}. {task_name}\n"
                
                group_issue_data = {
                    'title': f"[{project_title}] {group_name}",
                    'body': group_issue_body,
                    'labels': ['kensho-project', 'epic']
                }
                
                # Create the group issue
                response = requests.post(api_url, headers=headers, json=group_issue_data)
                
                if response.status_code == 201:
                    group_issue = response.json()
                    group_issue_number = group_issue['number']
                    logging.info(f"Created group issue #{group_issue_number}: {group_name}")
                    total_issues_created += 1
                    
                    # Create individual task issues
                    for task in tasks:
                        task_name = task.get('task_name', 'Unnamed Task')
                        task_details = task.get('details', '')
                        task_owner = task.get('owner', '')
                        
                        task_body = f"**Project:** {project_title}\n"
                        task_body += f"**Group:** {group_name}\n\n"
                        
                        if task_details:
                            task_body += f"**Details:** {task_details}\n\n"
                            
                        if task_owner:
                            task_body += f"**Assigned to:** {task_owner}\n\n"
                            
                        task_body += f"**Related Epic:** #{group_issue_number}"
                        
                        task_issue_data = {
                            'title': f"[{project_title}] {task_name}",
                            'body': task_body,
                            'labels': ['kensho-project', 'task']
                        }
                        
                        # Add assignee if owner is a valid GitHub username
                        if task_owner and '@' not in task_owner:  # Simple check for username vs email
                            task_issue_data['assignees'] = [task_owner]
                        
                        task_response = requests.post(api_url, headers=headers, json=task_issue_data)
                        
                        if task_response.status_code == 201:
                            task_issue = task_response.json()
                            task_issue_number = task_issue['number']
                            logging.info(f"Created task issue #{task_issue_number}: {task_name}")
                            total_issues_created += 1
                        else:
                            logging.error(f"Failed to create task issue '{task_name}': {task_response.status_code} - {task_response.text}")
                            
                else:
                    logging.error(f"Failed to create group issue '{group_name}': {response.status_code} - {response.text}")
                    return False
                    
        logging.info(f"Successfully created {total_issues_created} GitHub issues for project '{project_title}'")
        return True
        
    except KeyError as e:
        logging.error(f"Missing GitHub configuration section: {e}")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"GitHub API request failed: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error creating GitHub issues: {e}")
        return False