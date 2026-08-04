import os
import subprocess
import requests
import base64
import json
from datetime import datetime

# def generate_junit_xml(pytest_args=None, xml_path="results.xml"):
# 	"""Run pytest and generate JUnit XML results."""
# 	args = ["py", "-m", "pytest", "-v", "-s", f"--junitxml={xml_path}"]
# 	if pytest_args:
# 		args.extend(pytest_args)
# 	result = subprocess.run(args, capture_output=True, text=True)
# 	print(result.stdout)
# 	print(result.stderr)
# 	if result.returncode != 0:
# 		print("Pytest run failed.")
# 	return result.returncode

def create_test_execution(jira_domain, jira_user, jira_token, project_key, summary):
    url = f"https://{jira_domain}/rest/api/2/issue"
    auth = base64.b64encode(f"{jira_user}:{jira_token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    body = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": "Test Execution"}
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(body))
    if response.status_code != 201:
        print("Jira response:", response.text)
    response.raise_for_status()
    key = response.json()["key"]
    print(f"Created Test Execution: {key}")
    return key

# def upload_junit_to_xray(jira_domain, jira_user, jira_token, test_exec_key, xml_path):
# 	url = f"https://{jira_domain}/rest/raven/cloud/1.0/import/execution/junit?testExecKey={test_exec_key}"
# 	auth = base64.b64encode(f"{jira_user}:{jira_token}".encode()).decode()
# 	headers = {
# 		"Authorization": f"Basic {auth}"
# 	}
# 	with open(xml_path, "rb") as f:
# 		files = {"file": (os.path.basename(xml_path), f, "application/xml")}
# 		response = requests.post(url, headers=headers, files=files)
# 	response.raise_for_status()
# 	print(f"Uploaded results to Test Execution: {test_exec_key}")

XRAY_BASE_URL = "https://xray.cloud.getxray.app"
def get_xray_token(client_id, client_secret):
    url = f"{XRAY_BASE_URL}/api/v2/authenticate"
    response = requests.post(url, json={
        "client_id": client_id,
        "client_secret": client_secret
    })
    response.raise_for_status()
    return response.text.strip('"')

def upload_junit_to_xray_cloud(client_id, client_secret, test_exec_key, xml_path):
    token = get_xray_token(client_id, client_secret)
    url = f"{XRAY_BASE_URL}/api/v2/import/execution/junit?testExecKey={test_exec_key}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "text/xml"
    }
    with open(xml_path, "rb") as f:
        response = requests.post(url, headers=headers, data=f)

    response.raise_for_status()
    print(f"Uploaded results to Test Execution: {test_exec_key}")

# if __name__ == "__main__":
#     try:
#         jira_domain = os.environ.get("JIRA_DOMAIN", "jira-opisystems.atlassian.net")
#         jira_user = os.environ.get("JIRA_USER")
#         jira_token = os.environ.get("JIRA_TOKEN")
#         project_key = os.environ.get("JIRA_PROJECT_KEY", "OB")
#         from datetime import datetime
#         summary = f"Automated Test Execution for OB-9298 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
#         xml_path = "results.xml"
#         # Only upload if results.xml exists
#         if os.path.exists(xml_path):
#             try:
#                 client_id = os.environ.get("XRAY_CLIENT_ID")
#                 client_secret = os.environ.get("XRAY_CLIENT_SECRET")
#                 test_exec_key = os.environ.get("XRAY_TEST_EXEC_KEY")
#                 xml_path = "results.xml"
#                 if os.path.exists(xml_path):
#                     upload_junit_to_xray_cloud(client_id, client_secret, test_exec_key, xml_path)
#                 else:
#                     print(f"JUnit XML result file {xml_path} not found, skipping Xray upload.")
#             except Exception as e:
#                 print(f"Failed to upload results to Xray: {e}")
#         else:
#             print(f"JUnit XML result file {xml_path} not found, skipping Xray upload.")
#     except Exception as e:
#         print(f"Failed to upload results to Xray: {e}")
