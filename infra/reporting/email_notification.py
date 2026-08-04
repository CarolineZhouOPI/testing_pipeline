import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import requests
import base64

def send_email(subject, body, to_emails, attachment_path=None):
    # SMTP server configuration (Gmail example)
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = os.getenv('SMTP_SENDER_EMAIL')
    sender_password = os.getenv('SMTP_SENDER_PASSWORD')

    if not sender_email or not sender_password:
        raise ValueError('SMTP_SENDER_EMAIL and SMTP_SENDER_PASSWORD must be set as environment variables.')

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ', '.join(to_emails)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Attach file if provided
    if attachment_path and os.path.exists(attachment_path):
        part = MIMEBase('application', 'octet-stream')
        with open(attachment_path, 'rb') as f:
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_path)}')
        msg.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_emails, msg.as_string())
        server.quit()
        print('Email sent successfully!')
    except Exception as e:
        print(f'Failed to send email: {e}')


def send_email_sendgrid(subject, body, to_emails, attachment_path=None):
    """
    Send an email using SendGrid API.
    Requires SENDGRID_API_KEY and SENDGRID_SENDER_EMAIL to be set as environment variables.
    """
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    sender_email = os.getenv('SENDGRID_SENDER_EMAIL')
    if not sendgrid_api_key or not sender_email:
        raise ValueError('SENDGRID_API_KEY and SENDGRID_SENDER_EMAIL must be set as environment variables.')

    message = {
        "personalizations": [
            {"to": [{"email": email} for email in to_emails]}
        ],
        "from": {"email": sender_email},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": body}
        ]
    }

    # Attach file if provided
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            file_content = base64.b64encode(f.read()).decode()
        filename = os.path.basename(attachment_path)
        message["attachments"] = [
            {
                "content": file_content,
                "type": "application/octet-stream",
                "filename": filename,
                "disposition": "attachment"
            }
        ]

    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {sendgrid_api_key}",
            "Content-Type": "application/json"
        },
        json=message
    )
    if response.status_code == 202:
        print("SendGrid email sent successfully!")
    else:
        print(f"Failed to send email via SendGrid: {response.status_code} {response.text}")


if __name__ == "__main__":
    # Simple test: update these values as needed
    subject = 'QA Automation Results Test'
    body = 'This is a test email from the QA automation script.'
    to_emails = ['carolinez@opisystems.com']  # Replace with your email(s)
    attachment_path = None  # Or provide a path to a file, e.g., 'allure_report_zip.zip'
    # Uncomment to test Gmail SMTP
    send_email(subject, body, to_emails, attachment_path)
    # Test SendGrid
    # send_email_sendgrid(subject, body, to_emails, attachment_path)
