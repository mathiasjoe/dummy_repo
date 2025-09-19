import requests
import sys

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

if __name__ == "__main__":
    polaris_url = "https://eu.polaris.blackduck.com"
    api_token = input("Enter your Polaris API token: ").strip()
    session = createSession(polaris_url, api_token)
    projects_data = fetch_projects(session, polaris_url)
    projects = projects_data.get('_items', [])
    if not projects:
        print("No projects found.")
        sys.exit(1)
    print("Available projects:")
    for idx, proj in enumerate(projects):
        print(f"{idx}: {proj.get('name')} (ID: {proj.get('id')})")

