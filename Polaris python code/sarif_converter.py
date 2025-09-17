import json

# I have tried to maka an easy converter from JSON to SARIF format.
# Denner er kun i bruk for testing og proof of concept

# Load your issues
with open("issues_output.json") as f:
    issues = json.load(f)

# Build SARIF skeleton
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

# Map issues to SARIF results
for issue in issues:
    rule_id = issue.get("issueType", "PolarisIssue")
    message = issue.get("message", str(issue))
    location = issue.get("location", {})
    file_path = location.get("filePath", "UNKNOWN")
    line = location.get("line", 1)

    # Add rule if not already present
    if not any(r["id"] == rule_id for r in sarif["runs"][0]["tool"]["driver"]["rules"]):
        sarif["runs"][0]["tool"]["driver"]["rules"].append({
            "id": rule_id,
            "name": rule_id,
            "shortDescription": {"text": rule_id}
        })

    sarif["runs"][0]["results"].append({
        "ruleId": rule_id,
        "message": {"text": message},
        "locations": [{
            "physicalLocation": {
                "artifactLocation": {"uri": file_path},
                "region": {"startLine": line}
            }
        }]
    })

# Write SARIF file
with open("polaris_issues.sarif", "w") as f:
    json.dump(sarif, f, indent=2)

print("SARIF file written to polaris_issues.sarif")