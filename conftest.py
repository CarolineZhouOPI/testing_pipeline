import subprocess
import sys
import os
import glob
import shutil
from infra.reporting import xray_result_upload

def pytest_sessionfinish(session, exitstatus):
    """Generate Allure report once after the final test session."""
    if os.environ.get("GENERATE_ALLURE_REPORT") != "1":
        return

    if os.environ.get("PYTEST_XDIST_WORKER"):
        return

    print("\nGenerating Allure report...")

    allure_bin = shutil.which("allure")
    if not allure_bin:
        print("Skipping Allure report generation: 'allure' CLI not found in PATH.")
        return

    result_files = glob.glob(os.path.join("allure_results", "*.json"))
    if not result_files:
        print("Skipping Allure report generation: no files found in allure_results.")
        return

    env = os.environ.copy()
    java_home = env.get("JAVA_HOME")
    if java_home and not os.path.isdir(java_home):
        if shutil.which("java"):
            print(
                f"Warning: JAVA_HOME is invalid ('{java_home}'). "
                "Using java from PATH for Allure generation."
            )
            env.pop("JAVA_HOME", None)
        else:
            print(
                f"Skipping Allure report generation: JAVA_HOME is invalid ('{java_home}') "
                "and no java executable was found in PATH."
            )
            return

    try:
        result = subprocess.run([
            allure_bin, "generate", "allure_results", "--clean", "-o", "allure_report"
        ], check=True, capture_output=True, text=True, env=env)
        print(result.stdout)
        print(result.stderr)
        # --- ZIP THE ALLURE REPORT FOLDER ---
        allure_report_dir = "allure_report"
        zip_name = "allure_report_zip"
        shutil.make_archive(zip_name, 'zip', allure_report_dir)
        print(f"Allure report zipped as {zip_name}.zip")
    except subprocess.CalledProcessError as e:
        print(f"Failed to generate Allure report (exit code {e.returncode}).")
        if e.stdout:
            print("Allure stdout:")
            print(e.stdout)
        if e.stderr:
            print("Allure stderr:")
            print(e.stderr)
    except Exception as e:
        print(f"Failed to generate Allure report: {e}")
        
    try:
        from infra.reporting import xray_result_upload
        import datetime
        jira_domain = os.getenv("JIRA_DOMAIN", "jira-opisystems.atlassian.net")
        jira_user = os.getenv("JIRA_USER")
        jira_token = os.getenv("JIRA_TOKEN")
        project_key = os.getenv("JIRA_PROJECT_KEY", "OB")
        summary = f"Automated Test Execution - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        xml_path = os.path.join(os.path.dirname(__file__), "results.xml")

        if not jira_user or not jira_token:
            print("JIRA_USER/JIRA_TOKEN not set, skipping Xray execution creation and upload.")
            return

        test_exec_key = xray_result_upload.create_test_execution(
            jira_domain, jira_user, jira_token, project_key, summary
        )
        print(f"Created test execution: {test_exec_key}")
        # Upload JUnit results to Xray Cloud
        client_id = os.getenv("XRAY_CLIENT_ID")
        client_secret = os.getenv("XRAY_CLIENT_SECRET")
        if client_id and client_secret and os.path.exists(xml_path):
            xray_result_upload.upload_junit_to_xray_cloud(client_id, client_secret, test_exec_key, xml_path)
            print(f"Uploaded results.xml to Xray Cloud for execution {test_exec_key}")
        else:
            print("XRAY_CLIENT_ID/SECRET not set or results.xml missing, skipping upload.")
    except Exception as e:
        print(f"Failed to create test execution or upload results to Xray: {e}")

    # # --- EMAIL NOTIFICATION ---
    # try:
    #     from infra.reporting import email_notification
    #     subject = f"QA Automation Results - Automated Test Execution"
    #     body = f"The QA automation run is complete."
    #     to_emails = ['carolinez@opisystems.com']
    #     attachment_path = None

    #     email_notification.send_email(subject, body, to_emails, attachment_path)
    # except Exception as e:
    #     print(f"Failed to send email notification: {e}")



import pytest

# Example fixture
def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="dev", help="Environment to run tests against")

@pytest.fixture(scope="session")
def env(request):
    return request.config.getoption("--env")


# Fixture for MQTT credentials and device info
@pytest.fixture(scope="session")
def mqtt_test_config():
    return {
        "root_ca_path": os.getenv("MQTT_ROOT_CA_PATH", "infra/messaging/dev_qa_root_cert_auth.crt"),
        "cert_path": os.getenv("MQTT_CERT_PATH", "infra/messaging/dev_qa_client.crt"),
        "private_key_path": os.getenv("MQTT_KEY_PATH", "infra/messaging/dev_qa_client.key"),
        "client_id": os.getenv("MQTT_CLIENT_ID", ""),
        "mac_address": os.getenv("MQTT_MAC_ADDRESS", "")
    }

# # Utility to extract readings for moisture cable 3 and omni cable 4 from AllReportsV3 messages
# def extract_moisture3_omni4_readings(messages):
#     readings = []
#     for msg_type, decoded in messages:
#         if msg_type == "AllReportsV3":
#             for reading in decoded.readings:
#                 header = getattr(reading, "header", None)
#                 ts = getattr(header, "timestamp", None) if header else None
#                 for cable in reading.cable_readings:
#                     # Identify cable type and number
#                     types = cable.type if hasattr(cable.type, '__iter__') and not isinstance(cable.type, str) else [cable.type]
#                     cable_num = getattr(cable, "cable_num", None)
#                     # MOISTURE cableNum 3
#                     if (any(str(t).upper() == "MOISTURE" for t in types) or 2 in [int(t) for t in types if str(t).isdigit()]) and cable_num == 3:
#                         readings.append({
#                             "timestamp": ts,
#                             "type": "moisture",
#                             "tempReadings": list(getattr(cable, "temp_readings", [])),
#                             "rhReadings": list(getattr(cable, "rh_readings", [])),
#                         })
#                     # OMNI cableNum 4
#                     if (any(str(t).upper() == "OMNI" for t in types) or 3 in [int(t) for t in types if str(t).isdigit()]) and cable_num == 4:
#                         readings.append({
#                             "timestamp": ts,
#                             "type": "omni",
#                             "tempReadings": list(getattr(cable, "temp_readings", [])),
#                             "rhReadings": list(getattr(cable, "rh_readings", [])),
#                         })
#     return readings

# # Run MQTT collector for 24 hours and extract readings
# def run_mqtt_collector_and_extract(mqtt_config, duration_hours=24):
#     from infra.messaging.mqtt_collector import MQTTCollector
#     import time
#     collector = MQTTCollector(
#         mqtt_config["root_ca_path"],
#         mqtt_config["cert_path"],
#         mqtt_config["private_key_path"],
#         mqtt_config["client_id"],
#         mqtt_config["mac_address"]
#     )
#     collector.start()
#     print(f"Collecting MQTT messages for {duration_hours} hours...")
#     time.sleep(duration_hours * 3600)
#     messages = collector.collect_messages()
#     readings = extract_moisture3_omni4_readings(messages)
#     return readings