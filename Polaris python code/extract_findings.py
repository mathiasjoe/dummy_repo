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
    print(f"Found {len(projects)} projects:")
    for idx, proj in enumerate(projects):
        app = proj.get('application', {})
        #print(f"[{idx}] Project: {proj.get('name')} (ID: {proj.get('id')}) | App: {app.get('name')} (ID: {app.get('id')})")

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

    # Lag SARIF fil
    sarif = {
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "Polaris Custom Import",
                    "informationUri": "https://www.synopsys.com/",
                    "rules": []
                }
            },
            "results": []
        }]
    }

    for issue in issues:
        rule_id = str(issue.get("issueType", "PolarisIssue"))[:255]
        rule_title = str(issue.get("title", rule_id))
        description = str(issue.get("description", "No description provided."))
        remediation = str(issue.get("remediation", ""))
        file_path = issue.get("location", {}).get("filePath", "UNKNOWN")
        line = issue.get("location", {}).get("line", 1)
        severity = str(issue.get("severity", "warning")).lower()

        # Add rule if not already present
        rules = sarif["runs"][0]["tool"]["driver"]["rules"]
        if not any(r["id"] == rule_id for r in rules):
            rules.append({
                "id": rule_id,
                "name": rule_title,
                "shortDescription": {"text": rule_title},
                "fullDescription": {"text": description},
                "help": {
                    "text": remediation or "See documentation for remediation steps.",
                    "markdown": True
                },
                "helpUri": "https://owasp.org/www-community/Improper_Error_Handling"
            })

        sarif["runs"][0]["results"].append({
            "ruleId": rule_id,
            "message": {"text": f"{rule_title} at {file_path}:{line}.\n{description}"},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": file_path},
                    "region": {"startLine": line}
                }
            }],
            "properties": {
                "severityLevel": severity
            }
        })

    with open("polaris_issues.sarif", "w") as f:
        json.dump(sarif, f, indent=2)
    print("SARIF file written to polaris_issues.sarif")

if __name__ == "__main__":
    main()
    
        