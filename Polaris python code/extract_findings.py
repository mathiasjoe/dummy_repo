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
        print("Usage: python extract_findings.py <polaris_url> <api_token> [project_id]")
        sys.exit(1)

    url = sys.argv[1]
    token = sys.argv[2]

    session = createSession(url, token)
    projects_data = fetch_projects(session, url)
    projects = projects_data.get('_items', [])
    if not projects:
        print("No projects found.")
        sys.exit(1)

    if len(sys.argv) > 3:
        project_id = sys.argv[3]
    else:
        project_id = projects[0].get('id')

    project_ids = [proj.get('id') for proj in projects]
    if project_id not in project_ids:
        print(f"Invalid project_id {project_id}. Not found in available projects.")
        sys.exit(1)
    selected_proj = next(proj for proj in projects if proj.get('id') == project_id)
    project_name = selected_proj.get('name')

    # Print all available projects with their index, name, and ID
    #print("Available projects:")
    #for idx, proj in enumerate(projects):
        #print(f"{idx}: {proj.get('name')} (ID: {proj.get('id')})")

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
                    "name": "DAST-Scanner",
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
        # Skip dismissed issues
        triage_props = issue.get("triageProperties", [])
        is_dismissed = False
        for prop in triage_props:
            if prop.get("key") == "is-dismissed" and prop.get("value") is True:
                is_dismissed = True
                break
        if is_dismissed:
            continue

        # Skip informational severity and extract needed properties
        occurrence_props = issue.get("occurrenceProperties", [])
        is_informational = False
        severity = None
        cwe = None
        overall_score = None
        for prop in occurrence_props:
            if prop.get("key") == "severity":
                severity = str(prop.get("value", ""))
                if severity.lower() == "informational":
                    is_informational = True
            elif prop.get("key") == "cwe":
                cwe = prop.get("value")
            elif prop.get("key") == "overall-score":
                overall_score = prop.get("value")
        if is_informational:
            continue

        # Use issue ID as rule id, but include CWE in rule name if present
        rule_id = str(issue.get("id", "PolarisIssueID"))[:255]
        issue_type = issue.get("type", {})
        base_rule_name = issue_type.get("altName", "Polaris Issue")
        rule_name = f"{base_rule_name} ({cwe})" if cwe else base_rule_name
        description = None
        localized = issue_type.get("_localized", {})
        if isinstance(localized, dict):
            other_details = localized.get("otherDetails", [])
            if isinstance(other_details, list):
                for detail in other_details:
                    if detail.get("key") == "description":
                        description = detail.get("value")
                        break

        # Use a human-readable message
        message = issue.get("message")
        if not message:
            message = rule_name

        location = issue.get("location", {})
        file_path = location.get("filePath", "POLARIS")
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
            rule_entry = {
                "id": rule_id,
                "name": rule_name,
                "shortDescription": {
                    "text": rule_name
                },
                "fullDescription": {
                    "text": (description if description else rule_name)[:200],
                    "markdown": "[Visit Polaris for more information](https://eu.polaris.blackduck.com)"
                },
                "helpUri": "https://eu.polaris.blackduck.com",
                "help": {
                    "text": "Detailed explanation of the issue.",
                    
                }
            }
            if overall_score is not None:
                rule_entry["properties"] = {"security-severity": str(overall_score)}
            rules.append(rule_entry)
        else:
            rule_index = rule_id_map[rule_id]

       

        result = {
            "ruleId": rule_id,
            "ruleIndex": rule_index,
            "message": {
                "text": message
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
                }
            }],
        
        }
        if logical_name:
            result["locations"][0]["logicalLocations"] = [{"fullyQualifiedName": logical_name}]
        results.append(result)
    with open(sarif_path, "w") as f:
        json.dump(sarif, f, indent=2)
    print("SARIF file written to polaris_issues.sarif")

if __name__ == "__main__":
    main()

