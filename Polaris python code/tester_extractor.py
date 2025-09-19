import requests
import pprint
import json
import sys
import os
import re
'''
Copyright (c) 2024 Synopsys, Inc. All rights reserved worldwide. The information
contained in this file is the proprietary and confidential information of
Synopsys, Inc. and its licensors, and is supplied subject to, and may be used
only by Synopsys customers in accordance with the terms and conditions of a
previously executed license agreement between Synopsys and that customer.
'''

pp = pprint.PrettyPrinter(indent=4)

def createSession(url, token):
    headers = {'API-TOKEN': token}
    s = requests.Session()
    s.headers.update(headers)
    return s

def getresp(session, api, params=None, headers=None):
    if params == None:
        params = {}
    if headers == None:
        headers = {}
    response = session.get(api, params=params, headers=headers)
    # for debugging
    #print(f"API call: {response.url}")
    if (response.status_code >= 300):
        print("ERROR: GET failed: ", api)
        print("Response: ", response)
        try: pp.pprint(response.json())
        except: print("No json data returned")
        sys.exit(1)
    return(response.json())

# Given the _links from an API call, find the "next" and "first" links
# If one does not exist, return None
def getNextAndFirst(links):
   nextlink = None
   firstlink = None
   for l in links:
       if l['rel'] == 'next':
           nextlink = l['href']
       if l['rel'] == 'first':
           firstlink = l['href']

   return nextlink, firstlink

    
# General GET function that performs some basic error checking and returns the json
# Arguments:
#  - Session
#  - Polaris URL
#  - API URL
#  - parameters (optional)
#  - headers (optional)
# Returns:
#  The json contents (not paginated!)
def apiget(session, url, endpoint, params=None, headers=None):
    if params == None:
        params = {}
    api = url+endpoint
    json = getresp(session, api, params, headers)
    return(json)

# General GET function that performs some basic error checking and returns _items
# Arguments:
#  - Session
#  - Polaris URL
#  - API URL
#  - parameters (optional)
#  - headers (optional)
# Returns:
#  The _items returned by API
def apigetitems(session, url, endpoint, params=None, headers=None):
    if params == None:
        params = {}
    api = url+endpoint
    json = getresp(session, api, params, headers)
    
    data = json['_items']
    nextpage,firstpage = getNextAndFirst(json['_links'])
    while nextpage:
        if nextpage == firstpage:
            # Nothing to paginate, just return what we got.
            return(data)
        nextpage = fixAuthUrl(url, nextpage)
        # Fetch another page of data and append it
        json = getresp(session, nextpage)
        # Assumption: We are generally only interested in _items...
        data.extend(json['_items'])
        nextpage,firstpage = getNextAndFirst(json['_links'])
    return(data)


# Fetch Portfolio Id
# Arguments:
#  - Session
#  - Polaris URL
# Returns:
#  - Portfolio ID
def getPortfolioId(session, url):
    resp = apigetitems(session, url, "/api/portfolio/portfolios")
    return(resp[0]['id'])

# Fetch Application ID
# Arguments:
#  - Session
#  - Polaris URL
#  - Portfolio ID
#  - Application Name
# Returns:
#  - Application ID
def getApplicationId(session, url, pid, name):
    params = {}
    params['name'] = name
    resp = apigetitems(session, url,
      f"/api/portfolio/portfolios/{pid}/portfolio-items",
      params)
    try:
        return(resp[0]['id'])
    except:
        print(f"ERROR: Application {name} not found")
        sys.exit(1)

# Fetch Project ID
# Arguments:
#  - Session
#  - Polaris URL
#  - Application ID
#  - Project Name
# Returns:
#  - Project ID
def getProjectId(session, url, aid, name):
    params = {}
    params['name'] = name
    resp = apigetitems(session, url,
      f"/api/portfolio/portfolio-items/{aid}/portfolio-sub-items",
      params)
    try:
        return(resp[0]['id'])
    except:
        print(f"ERROR: Project {name} not found")
        sys.exit(1)

# Fetch Branch ID
# Arguments:
#  - Session
#  - Polaris URL
#  - Project ID
#  - Branch Name
#  - nonfatal? optional, will return None if branch not found.
#              otherwise, prints error message + exit code 1
# Returns:
#  - Branch ID
def getBranchId(session, url, pid, name, nonfatal=False):
    headers = {'content-type':
      "application/vnd.synopsys.pm.branches-1+json"}
    params = {'_filter' : f"name=={name}"}
    resp = apigetitems(session, url,
      f"/api/portfolio/portfolio-sub-items/{pid}/branches",
      params, headers)
    try:
        return(resp[0]['id'])
    except:
        if (nonfatal):
            return None
        else:
            print(f"ERROR: Branch {name} not found")
            sys.exit(1)

# Get Issues
# Arguments:
#  - Session
#  - Polaris URL
#  - Project ID
#  - Branch Id
#  - Parameters (Optional)
# Returns:
#  - raw issue data from API response
def getIssues(session, url, pid, bid, params=None):
    if params == None:
        params = {}
    params['portfolioSubItemId'] = pid
    params['branchId'] = bid
    params['_includeIssueProperties'] = 'true'
    params['_includeIssueType'] = 'true'
    params['_includeTriageProperties'] = 'true'
    resp = apigetitems(session, url,
      "/api/specialization-layer-service/issue-families/_actions/list",
      params)
    try:
        return(resp)
    except:
        # Not sure this is possible
        print(f"ERROR: No issues found")
        sys.exit(1)

def getNewIssues(session, url, pid, params=None):
    if params is None:
        params = {}
    params['projectId'] = pid
    params['_includeIssueProperties'] = 'true'
    params['_includeType'] = 'true'
    params['_includeTriageProperties'] = 'true'
    params['_includeContext'] = 'true' 
    resp = apigetitems(session, url,
      "/api/findings/issues",
      params)
    try:
        return(resp)
    except:
        print(f"ERROR: No issues found")
        sys.exit(1)

if __name__ == "__main__":
    # # Replace these with your actual values
    # polaris_url = "https://eu.polaris.blackduck.com"
    # api_token = "6omicioa5d1qb4uvgsmb9ndm21e69ks5om54r8s6kfk5fqffdkt4bct4a31f6vgsveuqo38k3v0u4"
    # project_id = "adbd0aed-b695-4b5d-ad05-0c603e12fe1d"

    # session = createSession(polaris_url, api_token)
    # issues = getNewIssues(session, polaris_url, project_id)
    # print(json.dumps(issues, indent=2))


    #Replace with your actual Polaris URL and API token
    polaris_url = "https://eu.polaris.blackduck.com"
    api_token = "6omicioa5d1qb4uvgsmb9ndm21e69ks5om54r8s6kfk5fqffdkt4bct4a31f6vgsveuqo38k3v0u4"

    session = createSession(polaris_url, api_token)

    # Fetch projects (adjust the endpoint/logic if your API is different)
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

    projects_data = fetch_projects(session, polaris_url)
    projects = projects_data.get('_items', [])
    if not projects:
        print("No projects found.")
        sys.exit(1)

    print("Available projects:")
    for idx, proj in enumerate(projects):
        print(f"{idx}: {proj.get('name')} (ID: {proj.get('id')})")

