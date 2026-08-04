# s3_logs_download_helper.py

import boto3
import botocore.session
import os
from datetime import datetime
import requests
from botocore.awsrequest import AWSResponse
from botocore.httpsession import URLLib3Session

# download_logs_from_s3(
#    bucket="your-bucket",
#    prefix="your/prefix/",
#    dest="local_folder",
#    mac_address="AA:BB:CC:DD:EE:FF",
#    start_time=start_dt,
#    end_time=end_dt,
#    client_cert="path/to/dev_qa_client.crt",
#    client_key="path/to/dev_qa_client.key",
#    root_ca="path/to/dev_qa_root_cert_auth.crt"
#)

def download_logs_from_s3(
    bucket, prefix, dest, mac_address, start_time, end_time,
    client_cert=None, client_key=None, root_ca=None
):
    """
    Download S3 logs filtered by MAC address and timeline.
    Args:
        bucket (str): S3 bucket name
        prefix (str): S3 prefix/folder for logs
        dest (str): Local destination directory
        mac_address (str): MAC address to filter logs
        start_time (datetime): Start of timeline
        end_time (datetime): End of timeline
    """
    # Set up mutual TLS if certs are provided
    if client_cert and client_key and root_ca:
        # Create a custom botocore session with mTLS
        session = botocore.session.get_session()
        # Patch the botocore session to use mTLS
        class MTLSUrlLib3Session(URLLib3Session):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._client_cert = (client_cert, client_key)
                self._ca_bundle = root_ca
            def send(self, request):
                # Use requests to send with mTLS
                resp = requests.request(
                    method=request.method,
                    url=request.url,
                    headers=request.headers,
                    data=request.body,
                    cert=self._client_cert,
                    verify=self._ca_bundle,
                    stream=True
                )
                raw = resp.raw
                return AWSResponse(
                    request.url, resp.status_code, resp.headers, raw
                )
        session.set_config_variable('s3', {'use_ssl': True})
        s3 = session.create_client(
            's3',
            aws_access_key_id=None,
            aws_secret_access_key=None,
            use_ssl=True,
            verify=root_ca
        )
        s3._endpoint.http_session = MTLSUrlLib3Session()
    else:
        s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    if not os.path.exists(dest):
        os.makedirs(dest)
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            # Filter by timeline if key contains date, or use LastModified
            last_modified = obj['LastModified']
            if not (start_time <= last_modified <= end_time):
                continue
            # Download the file
            local_path = os.path.join(dest, os.path.basename(key))
            s3.download_file(bucket, key, local_path)
            # Filter by MAC address in file
            with open(local_path, 'r') as f:
                lines = f.readlines()
            filtered_lines = [line for line in lines if mac_address.lower() in line.lower()]
            if filtered_lines:
                with open(local_path, 'w') as f:
                    f.writelines(filtered_lines)
            else:
                os.remove(local_path)
    print(f"Download complete. Logs with MAC {mac_address} from {start_time} to {end_time} saved to {dest}")
