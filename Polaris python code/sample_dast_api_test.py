import requests
from pprint import pprint as p

url = 'https://polaris.blackduck.com'
token = 'redacted'

header_test = {
    'Content-Type': 'application/vnd.polaris.tests.tests-bulk-create-1+json',
    'Api-token': token
}

body_test = {
    "applicationId": "e09ac879-1dd2-4233-be81-be6c6a687a6e",
    "projectId": "dbad022c-9927-4d3c-91c0-1beb72b1e0dd",
    "notes": "This scan is for JuiceShop project",
    "assessmentTypes": [
    "DAST"
    ],
    "testMode": "DAST_WEBAPP",
    "triage": "NOT_REQUIRED",
    "profileDetails": {
        "id": "1739961c-fe23-4ce4-8d1e-fa5fb5e8e02c"
    }
}

#INITIATE TEST
session = requests.post(url+'/api/tests',headers=header_test, json=body_test)
p(session.json())