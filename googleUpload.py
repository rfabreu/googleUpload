import requests
import tempfile
import os
import time
from tqdm import tqdm
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
from slackNotify import send_notification

load_dotenv()

# Environment variables for sensitive information
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
FOLDER_ID = os.getenv("FOLDER_ID")

# Ensure required environment variables are set
if not all([SERVICE_ACCOUNT_FILE, FOLDER_ID]):
    raise EnvironmentError(
        "Missing required environment variables. Please set SERVICE_ACCOUNT_FILE and FOLDER_ID."
    )

# Set up Google Drive API
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/drive']
)
drive_service = build('drive', 'v3', credentials=credentials)

# Constants for handling large uploads
CHUNK_SIZE = 10 * 1024 * 1024  # 10MB chunk size
TIMEOUT_SECONDS = 300  # Timeout if no progress in 5 minutes
MAX_RETRIES = 5  # Maximum retry attempts

def send_email_notification(to_emails, cc_emails, bcc_emails, subject, reply_email):
    """Send a single confirmation email after all uploads."""
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = os.getenv("SMTP_USER")  # Email address
    smtp_password = os.getenv("SMTP_PASSWORD")  # App-specific password

    message_body = f"""Dear Partner,

The recordings of today's HBCUGO event have been uploaded to the shared drive. They should now be available for download.

If you have any questions or concerns, please do not hesitate to contact us at {reply_email}.

Thank you."""

    msg = MIMEText(message_body)
    msg["Subject"] = subject
    msg["From"] = smtp_user

    # Add recipients to appropriate fields
    msg["To"] = ", ".join(to_emails)
    if cc_emails:
        msg["Cc"] = ", ".join(cc_emails)
    if bcc_emails:
        msg["Bcc"] = ", ".join(bcc_emails)

    all_recipients = to_emails + cc_emails + bcc_emails

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, all_recipients, msg.as_string())
        print("Email notification sent successfully.")
    except smtplib.SMTPAuthenticationError as auth_error:
        print(f"SMTP Authentication Error: {auth_error}")
    except Exception as e:
        print(f"Failed to send email notification: {e}")

def upload_large_file(file_name, file_url, custom_name):
    """Download and upload large files from HyperDeck to Google Drive with progress tracking."""
    start_time = datetime.now()
    print(f"[{start_time}] Starting download and upload for: {file_name}")

    # Notify Slack of download start
    send_notification(f"Starting download for: {custom_name}{os.path.splitext(file_name)[1]}")

    # Set up Google Drive upload metadata
    mime_type = 'video/quicktime' if file_name.endswith('.mov') else 'application/x-mcc'
    new_name = f"{custom_name}{os.path.splitext(file_name)[1]}"
    file_metadata = {'name': new_name, 'parents': [FOLDER_ID]}

    # Get the total file size
    with requests.head(file_url) as head_response:
        total_size = int(head_response.headers.get('content-length', 0))

    print(f"Starting download for: {file_name} (Total Size: {total_size / (1024 * 1024):.2f} MB)")

    # Temporary file for download
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file_path = temp_file.name

        # Download the file
        start_timer = time.time()  # Timer for periodic notifications
        with requests.get(file_url, stream=True) as r, tqdm(total=total_size, unit='B', unit_scale=True,
                                                            desc=f"Downloading {file_name}") as pbar:
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    temp_file.write(chunk)
                    pbar.update(len(chunk))

                # Notify every 10 minutes
                if time.time() - start_timer >= 600:
                    send_notification(f"Download in progress for: {custom_name}{os.path.splitext(file_name)[1]}")
                    start_timer = time.time()

        print(f"Download complete for {file_name}. Temporary file saved at: {temp_file_path}")
        send_notification(f"Download complete for: {custom_name}{os.path.splitext(file_name)[1]}")

    # Notify Slack of upload start
    print(f"Starting upload for {new_name}...")
    send_notification(f"Starting upload for: {custom_name}{os.path.splitext(file_name)[1]}")

    with open(temp_file_path, 'rb') as file_stream:
        media = MediaIoBaseUpload(file_stream, mimetype=mime_type, chunksize=CHUNK_SIZE, resumable=True)
        request = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True
        )

        response = None
        start_timer = time.time()  # Reset timer for periodic notifications
        with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"Uploading {new_name}") as pbar:
            while response is None:
                try:
                    status, response = request.next_chunk()
                    if status:
                        progress_increment = status.resumable_progress - pbar.n
                        pbar.update(progress_increment)

                    # Notify every 10 minutes
                    if time.time() - start_timer >= 600:
                        send_notification(f"Upload in progress for: {custom_name}{os.path.splitext(file_name)[1]}")
                        start_timer = time.time()
                except Exception as e:
                    print(f"Error during upload: {e}")
                    time.sleep(5)

    if response:
        print(f"Upload complete for {new_name}")
        send_notification(f"Upload complete for: {custom_name}{os.path.splitext(file_name)[1]}")

    # Clean up the temporary file
    os.remove(temp_file_path)
    print(f"Temporary file {temp_file_path} deleted after upload.")

    end_time = datetime.now()
    elapsed_time = end_time - start_time
    print(f"[{end_time}] Completed processing for: {new_name}")
    print(f"Total elapsed time: {elapsed_time}")

def interactive_cli():
    """Interactive CLI to configure and process HyperDeck downloads/uploads."""
    # Prompt for HyperDeck IP or URL
    hyperdeck_ip = input("Enter the HyperDeck IP or URL: ").strip()
    hyperdeck_url = f"http://{hyperdeck_ip}/mounts/"
    print(f"Connecting to HyperDeck at {hyperdeck_url}...")

    # Fetch and display folders
    response = requests.get(hyperdeck_url)
    if response.status_code != 200:
        print("Failed to connect to HyperDeck. Please check the IP or URL.")
        return

    folders = response.json()
    print("Available folders:")
    for idx, folder in enumerate(folders):
        print(f"{idx + 1}. {folder['name']}")

    # Select folder
    folder_index = int(input("Select a folder by number: ")) - 1
    folder_name = folders[folder_index]["name"]
    folder_url = f"{hyperdeck_url}{folder_name}/"
    print(f"Accessing folder: {folder_name}")

    # Fetch and display files
    response = requests.get(folder_url)
    files = response.json()
    print("Available files:")
    for idx, file_info in enumerate(files):
        print(f"{idx + 1}. {file_info['name']}")

    # Select files
    selected_files = input("Enter the file numbers to queue for download (comma-separated): ")
    selected_files = [files[int(idx) - 1] for idx in selected_files.split(",")]

    # Prompt for custom file name
    custom_name = input("Enter a custom name for the downloaded files (without extension): ").strip()

    # Prompt for email addresses and type
    email_addresses = input("Enter email addresses to notify (comma-separated): ").split(',')
    email_addresses = [email.strip() for email in email_addresses]

    email_type = input("Send emails as (To/Cc/Bcc): ").strip().lower()
    to_emails, cc_emails, bcc_emails = [], [], []

    if email_type == "to":
        to_emails = email_addresses
    elif email_type == "cc":
        cc_emails = email_addresses
    elif email_type == "bcc":
        bcc_emails = email_addresses
    else:
        print("Invalid email type selected. Defaulting to To.")
        to_emails = email_addresses

    # Prompt for email subject
    email_subject = input("Enter the subject line for the notification email: ").strip()

    # Prompt for reply email
    reply_email = input("Enter the reply-back email address: ").strip()

    # Notify Slack when the download process actually starts
    send_notification(f"HyperDeck upload process started for: {custom_name}")

    # Process each selected file
    for file_info in selected_files:
        file_name = file_info["name"]
        file_url = f"{folder_url}{file_name}"
        upload_large_file(file_name, file_url, custom_name)

    # Notify Slack of process completion
    send_notification(f"HyperDeck upload process completed for: {custom_name}")

    # Send email notification after all uploads
    send_email_notification(
        to_emails=to_emails,
        cc_emails=cc_emails,
        bcc_emails=bcc_emails,
        subject=email_subject,
        reply_email=reply_email
    )

if __name__ == "__main__":
    interactive_cli()