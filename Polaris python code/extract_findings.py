import requests
import sys

import json

import polarislib

def createSession(url, token):
    headers = {'API-TOKEN': token}
    s = requests.Session()
    s.headers.update(headers)
    return s

def fetch_projects(session, url, limit=100):
    endpoint = f"/api/portfolios/074b4f38-ece1-4091-aa9e-637925491dbc/projects?_limit={limit}"
    headers = {
        "accept": "application/vnd.polaris.portfolios.projects-1+json"
    }
    response = session.get(url + endpoint, headers=headers)
    if response.status_code != 200:
        print("Failed to fetch projects:", response.status_code)
        print(response.text)
        sys.exit(1)
    return response.json()

def main():
    if len(sys.argv) < 3:
        print("Usage: python extract_findings.py <polaris_url> <api_token> [project_index]")
        sys.exit(1)

    url = sys.argv[1]
    token = sys.argv[2]
    project_index = 0
    if len(sys.argv) > 3:
        try:
            project_index = int(sys.argv[3])
        except ValueError:
            print("Invalid project_index. It must be an integer.")
            sys.exit(1)

    session = createSession(url, token)
    projects_data = fetch_projects(session, url)
    projects = projects_data.get('_items', [])
    if not projects:
        print("No projects found.")
        sys.exit(1)
    if project_index < 0 or project_index >= len(projects):
        print(f"Invalid project_index {project_index}. Must be between 0 and {len(projects)-1}.")
        sys.exit(1)
    selected_proj = projects[project_index]
    project_id = selected_proj.get('id')
    project_name = selected_proj.get('name')

    # Remove old output files if they exist
    import os
    json_path = "issues_output.json"
    sarif_path = "polaris_issues.sarif"
    for path in [json_path, sarif_path]:
        if os.path.exists(path):
            os.remove(path)

    # Fetch issues from the selected project
    issues = polarislib.getIssues(session, url, project_id, None)
    print(f"\nFound {len(issues)} issues for project '{project_name}':")
    with open(json_path, "w") as f:
        json.dump(issues, f, indent=2)
    print(f"Issues written to {json_path}")

    # Build SARIF file in the requested format
    sarif = {
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "CodeScanner",
                    "rules": []
                }
            },
            "artifacts": [],
            "results": []
        }]
    }

    rule_id_map = {}  # Map rule_id to ruleIndex
    artifact_map = {}  # Map file_path to artifact index
    rules = sarif["runs"][0]["tool"]["driver"]["rules"]
    artifacts = sarif["runs"][0]["artifacts"]
    results = sarif["runs"][0]["results"]

    for issue in issues:
        rule_id = str(issue.get("issueType", "PolarisIssue"))[:255]
        message = str(issue.get("message", str(issue)))
        location = issue.get("location", {})
        file_path = location.get("filePath", "UNKNOWN")
        line = location.get("line", 1)
        logical_name = issue.get("function", None) or issue.get("logicalLocation", None)

        # Add artifact if not already present
        if file_path not in artifact_map:
            artifact_index = len(artifacts)
            artifact_map[file_path] = artifact_index
            artifacts.append({
                "location": {
                    "uri": file_path,
                    "uriBaseId": "SRCROOT"
                },
                "sourceLanguage": "python"
            })
        else:
            artifact_index = artifact_map[file_path]

        # Add rule if not already present
        if rule_id not in rule_id_map:
            rule_index = len(rules)
            rule_id_map[rule_id] = rule_index
            rules.append({
                "id": rule_id,
                "fullDescription": {
                    "text": message
                },
                "messageStrings": {
                    "default": {
                        "text": message
                    }
                }
            })
        else:
            rule_index = rule_id_map[rule_id]

        result = {
            "ruleId": rule_id,
            "ruleIndex": rule_index,
            "message": {
                "id": "default",
                "arguments": [message]
            },
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": file_path,
                        "uriBaseId": "SRCROOT",
                        "index": artifact_index
                    },
                    "region": {
                        "startLine": line
                    }
                },
                "logicalLocations": ([{
                    "fullyQualifiedName": logical_name
                }] if logical_name else [])
            }]
        }
        results.append(result)

    with open(sarif_path, "w") as f:
        json.dump(sarif, f, indent=2)
    print("SARIF file written to polaris_issues.sarif")

if __name__ == "__main__":
    main()
    
        