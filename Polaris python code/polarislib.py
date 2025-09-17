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


def fixAuthUrl(url, nextUrl):
    # The auth endpoint can return non-funtional links.
    # Insert the "/api/auth" so they work.
    regex = re.escape(url) + r'/users(.*)'
    match = re.match(regex, nextUrl)
    if match is None: return(nextUrl)
    # If the URL is of the form "url/users" it needs to be converted to
    # "(url)/api/auth/users"
    fixedUrl =  url + "/api/auth/users" + match.group(1)
    return fixedUrl
    
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

# General POST function 
# Arguments:
#  - Session
#  - Polaris URL
#  - API URL
#  - Json body to POST
#  - content-type header to set
# Returns:
#  - The API json response,  if relevant
def apipost(session, url, endpoint, body, contentType):
    headers = {'content-type': contentType}
    response = session.post(url + endpoint, headers=headers, data=json.dumps(body))
    if (response.status_code == 409):
        # This means the item already exists
        try: print("WARNING: ", response.json()['detail'])
        except: print("No detail provided")
        return(response.json())
    if (response.status_code >= 300):
        print(f"ERROR: POST failed: endpoint={endpoint}, body={body}")
        print("Response: ", response)
        print(f"endpoint: {url + endpoint}")
        print(f"body: {body}")
        print(f"headers: {headers}")
        try: pp.pprint(response.json())
        except: print("No json data returned")
        sys.exit(1)
    if (response.status_code == 204):
        # No content but post was OK
        return
    else:
        return(response.json())

def apipatch(session, url, endpoint, body, contentType, params=None):
    headers = {'content-type': contentType}
    if params == None:
        params = {}
    response = session.patch(url + endpoint, headers=headers, json=body,
      params=params)
    if (response.status_code >= 300):
        print("ERROR: POST failed: ", endpoint, body)
        print("Response: ", response)
        try: pp.pprint(response.json())
        except: print("No json data returned")
        sys.exit(1)
    try: return(response.json())
    except: return None

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

# Lookup the global role IDs
# Arguments:
# - session
# - url
# Returns:
# - Dictionary of roles, keyed on the human-readable name
def getRoles(session, url):
    resp = apigetitems(session, url, "/api/ciam/roles")
    roles = {}
    for item in resp:
        roles[item['name']] = item['id']
    return(roles)

# Lookup the application role IDs
# Arguments:
# - session
# - url
# Returns:
# - Dictionary of roles, keyed on the human-readable name
def getAppRoles(session, url):
    resp = apigetitems(session, url, "/api/ciam/resources/applications/roles")
    roles = {}
    for item in resp:
        roles[item['name']] = item['id']
    return(roles)

# Lookup an individual user's roles
# Arguments:
# - session
# - url
# - userid
# Returns:
# - Dictionary of roles, keyed on the human-readable name
# (NOTE: this should be exactly 1 role)
def getUserRoles(session, url, userid):
    resp = apigetitems(session, url, f"/api/ciam/users/{userid}/roles")
    roles = {}
    for item in resp:
        roles[item['name']] = item['id']
    return(roles)

# Lookup a user by their email address
# Arguments:
# - session
# - url
# - email
# Returns:
# - Userid if match, None if no match
def getUserId(session, url, email):
    params = {'_filter': f'email=={email}'}
    resp = apigetitems(session, url, f"/api/ciam/users", params=params)
    # Filtering on 1 email should result in exactly 1 response
    try: return(resp[0]['id'])
    except: return(None)

# Lookup a group ID by its name
# Arguments:
# - session
# - url
# - group name
# Returns:
# - Groupid if match, None if no match
def getGroupId(session, url, name):
    params = {'_filter': f'search=="{name}"'}
    resp = apigetitems(session, url, f"/api/ciam/groups", params=params)
    # Filtering on 1 name should result in exactly 1 response
    try: return(resp[0]['id'])
    except: return(None)

# Returns tenant id
def getTenantId(session, url):
    resp = apiget(session, url, "/api/ciam/openid-connect/userinfo")
    return(resp['organization']['id'])

# Return list of available subscription ids
# Arguments:
# - session
# - url
def getSubscriptions(session, url):
    params = {'_filter': 'isActive==true'}
    #  -H 'accept: application/vnd.synopsys.ses.entitlement-3+json' \
    #  -H 'content-type: application/vnd.synopsys.ses.entitlement-3+json' \
    headers = {'content-type': "application/vnd.synopsys.ses.subscription-2+json", \
               'accept': "application/vnd.synopsys.ses.subscription-2+json"}
    tenant = getTenantId(session, url)
    resp = apigetitems(session, url,
      f"/api/entitlement-service/tenants/{tenant}/subscriptions", params=params,
      headers=headers)
    subs = []
    for item in resp:
        subs.append(item['id'])
    return subs

# Return list of available entitelement ids
# Arguments:
# - session
# - url
# Returns:
# - list of entitlement Ids
def getEntitlements(session, url):
    params = {'_filter': 'isActive==true'}
    headers = {'content-type': "application/vnd.synopsys.ses.entitlement-3+json", \
               'accept': "application/vnd.synopsys.ses.entitlement-3+json"}
    tenant = getTenantId(session, url)
    resp = apigetitems(session, url,
      f"/api/entitlement-service/tenants/{tenant}/entitlements", params=params,
      headers=headers)
    entitle = []
    for item in resp:
        entitle.append(item['id'])
    return entitle

# Return Execution Mode of entitlement (parallel | concurrent)
# Note this is set per-entitlement. We assume all entitlements have the same
# execution mode and return the first value encountered.
#
# Arguments:
# - session
# - url
# Returns:
# - string: "PARALLEL" or "CONCURRENT"
#   -- or None if there are no valid subscriptions
def getExecutionMode(session, url):
    params = {'_filter': 'isActive==true'}
    headers = {'content-type': "application/vnd.synopsys.ses.entitlement-3+json", \
               'accept': "application/vnd.synopsys.ses.entitlement-3+json"}
    tenant = getTenantId(session, url)
    resp = apigetitems(session, url,
      f"/api/entitlement-service/tenants/{tenant}/entitlements", params=params,
      headers=headers)
    try: return(resp[0]['executionMode'].upper())
    except: return None

# Create a user
# Arguments:
# - session
# - url
# - email address
# - first name
# - last name
# Returns:
# - New user ID or None (user probably already existed)
def createUser(session, url, email, first, last):
    data = {
        'email': email,
        'firstName': first,
        'lastName': last,
        'enabled': 'true'
    }
    resp = apipost(session, url, "/api/ciam/users", data, 'application/vnd.synopsys.ciam.user-1+json')
    try:
        return(resp['id'])
    except:
        # Non-fatal warning, probably that the user already existed
        return None

# Set a user's global role
# Arguments:
# - session
# - url
# - user ID
# - desired role ID to set
# Returns:
# - Nothing
def setUserRole(session, url, userId, roleId):
    data = {
        'roles': [
          {
            'id': roleId
          }
        ]
    }
    # Success will return nothing
    # Failures should be reported in apipost
    resp = apipost(session, url, "/api/ciam/users/" + userId + "/roles", data, \
      'application/vnd.synopsys.ciam.user-role-1+json')

# Set a user's application role
# Arguments:
# - session
# - url
# - user ID
# - application ID
# - desired app role ID to set
# Returns:
# - Nothing
def setUserAppRole(session, url, userId, appId, roleId):
    data = {
        'userIds': [userId]
    }
    # Failures should be reported in apipost
    resp = apipost(session, url, "/api/ciam/resources/applications/" + appId + \
      "/roles/" + roleId + "/users", data, \
      'application/vnd.synopsys.ciam.application-role-user-1+json')

# Set a groups's application role
# Arguments:
# - session
# - url
# - group ID
# - application ID
# - desired app role ID to set
# Returns:
# - Nothing
def setGroupAppRole(session, url, groupId, appId, roleId):
    data = {
        'assignments': [{"groupId": groupId, "roleId": roleId}]
    }
    # Failures should be reported in apipost
    resp = apipost(session, url, "/api/ciam/applications/" + appId + \
      "/groups", data, \
      'application/vnd.synopsys.ciam.application-group-role-1+json')

# Create a group
# Arguments:
# - session
# - url
# - group name
# Returns:
# - New group ID or None (group probably already existed)
def createGroup(session, url, name):
    data = {
        'name': name,
    }
    resp = apipost(session, url, "/api/ciam/groups", data, 'application/vnd.synopsys.ciam.group-1+json')
    try:
        return(resp['id'])
    except:
        # Non-fatal warning, probably that the group already existed
        return None

# Add a user to a group
# TODO this could be a list of users...
# Arguments:
# - session
# - url
# - user id
# - group id
# Returns:
# - Nothing. apipatch exits with a fatal error if there was a non-successful patch
def addUserToGroup(session, url, userid, groupid):
    data = [{"userId":userid}]
    resp = apipatch(session, url, f"/api/ciam/groups/{groupid}/users", data,
      'application/vnd.synopsys.ciam.group-user-1+json')
    return

# Update existing issue with new triage data
# Arguments:
# - session
# - url
# - issue Id
# - project Id
# - branch Id
# - triage data (See format below)
# Returns:
# - Nothing. apipatch exits with a fatal error if there was a non-successful patch
def setTriage(session, url, issueId, projectId, branchId, data):
    # Data structure looks like this. We'll handle the filter/issueProperties part
    # based on the issueId provided.
    #
    #data = {
    #  "filter": "issueProperties:family-id=in=('DB1B88BDC162877F30E34DA0F579AA20')",
    #  "triageProperties": [
    #    {
    #      "key": "owner",
    #      "value": "1b0d3517-39ec-4107-83f3-29ebba6fd521"
    #    },
    #    {
    #      "key": "status",
    #      "value": "to-be-fixed"
    #    },
    #    {
    #      "key": "comment",
    #      "value": "a brave new comment!"
    #    }
    #  ]
    #}

    data['filter'] = f"issueProperties:family-id=in=('{issueId}')"
    params = {'projectId': projectId, 'branchId': branchId}
    contentType = "application/vnd.synopsys.polaris-one.issue-management.issue-family-bulk-triage-attributes-1+json"
    json = apipatch(session, url,
      f"/api/specialization-layer-service/issue-families", data, contentType,
      params)
    return

# Create an Application
# Arguments:
# - session
# - url
# - application name
# - application description (optional)
# Returns:
# - ID of created application, None for non-fatal errors
def createApplication(session, url, name, description=None):
    entitle = getEntitlements(session, url)
    exec = getExecutionMode(session, url)
    if exec is None:
        # This is a fatal error, we must have a valid subscription type
        print("ERROR: No valid subscription for tenant")
        sys.exit(1)
    data = {
        'name': name,
        'itemType': "APPLICATION",
        'description': description,
        'subscriptionTypeUsed': exec,
        'entitlements': {'entitlementIds' :  entitle }
    }
    portfolioId = getPortfolioId(session, url)

    resp = apipost(session, url, f"/api/portfolio/portfolios/{portfolioId}/portfolio-items", data,
      'application/vnd.synopsys.pm.portfolio-items-2+json')

    try:
        return(resp['id'])
    except:
        # Non-fatal warning, probably due to application already existing
        return None

# Create a Branch
# Assumptions: Not default branch, no auto-delete, no branch retention settings
# Arguments:
# - session
# - url
# - project id
# - branch description (optional)
# Returns:
# - ID of created branch, None for non-fatal errors
def createBranch(session, url, pid, name, description=None):
    data = {
        'name':name,
        'isDefault':"false",
        'source':"USER",
        'description':description,
        'autoDeleteSetting':"false",
        'branchRetentionPeriodSetting':None,
        'autoDeleteSettingsCustomized':None
    }

    portfolioId = getPortfolioId(session, url)

    resp = apipost(session, url, f"/api/portfolio/portfolio-sub-items/{pid}/branches", data,
      'application/vnd.synopsys.pm.branches-1+json')

    try:
        return(resp['id'])
    except:
        # Non-fatal warning, probably due to branch already existing
        return None

# Set project default policy on a branch
# Arguments:
# - session
# - url
# - branchId
# Returns: Nothing
def setBranchPolicyDefault(session, url, branchId):
    data = {
        "enable":"true",
        "inheritParentPolicies":"true",
        "associationId":branchId,
        "associationType":"branch",
        "assignedPolicies":[]
    }

    resp = apipost(session, url, "/api/policies/portfolio-policy-configuration", data,
      'application/vnd.synopsys.polaris.policy.portfolio-policy-configuration-1+json')
    # Success will return nothing
    # Failures should be reported in apipost
