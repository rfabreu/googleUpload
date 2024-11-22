# !!! NEW VERSION == FIXES DUPLICATED MESSAGES
# !!! ADDS ELAPSED TIME
import requests
import tempfile
import os
import time
from tqdm import tqdm
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime

# Environment variables for sensitive information
HYPERDECK_URL = os.getenv("HYPERDECK_URL")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
FOLDER_ID = os.getenv("FOLDER_ID")

# Ensure required environment variables are set
if not all([HYPERDECK_URL, SERVICE_ACCOUNT_FILE, FOLDER_ID]):
    raise EnvironmentError(
        "Missing required environment variables. Please set HYPERDECK_URL, SERVICE_ACCOUNT_FILE, and FOLDER_ID."
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


def upload_large_file(file_name, file_url):
    """Download and upload large files from HyperDeck to Google Drive with progress tracking."""

    start_time = datetime.now()  # Record the start time
    print(f"[{start_time}] Starting download and upload for: {file_name}")

    # Set up Google Drive upload metadata
    mime_type = 'video/quicktime' if file_name.endswith('.mov') else 'application/x-mcc'
    file_metadata = {'name': file_name, 'parents': [FOLDER_ID]}

    # Attempt to get the total file size
    with requests.head(file_url) as head_response:
        total_size = int(head_response.headers.get('content-length', 0))

    if total_size == 0:
        print(f"Warning: Unable to retrieve file size for {file_name}. Progress bar may not be accurate.")

    print(f"Starting download for: {file_name} (Total Size: {total_size / (1024 * 1024):.2f} MB if available)")

    # Temporary file for download
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file_path = temp_file.name

        # Download the file
        with requests.get(file_url, stream=True) as r, tqdm(total=total_size, unit='B', unit_scale=True,
                                                            desc=f"Downloading {file_name}") as pbar:
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    temp_file.write(chunk)
                    pbar.update(len(chunk))

        print(f"Download complete for {file_name}. Temporary file saved at: {temp_file_path}")

    # Upload the file
    print(f"Starting upload for {file_name}...")

    with open(temp_file_path, 'rb') as file_stream:
        media = MediaIoBaseUpload(file_stream, mimetype=mime_type, chunksize=CHUNK_SIZE, resumable=True)
        request = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True
        )

        response = None
        retry_count = 0
        uploaded_bytes = 0

        with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"Uploading {file_name}") as pbar:
            while response is None:
                try:
                    status, response = request.next_chunk()
                    if status:
                        progress_increment = status.resumable_progress - uploaded_bytes
                        pbar.update(progress_increment)
                        uploaded_bytes = status.resumable_progress
                except Exception as e:
                    retry_count += 1
                    print(f"Error during upload of {file_name} (retry {retry_count}/{MAX_RETRIES}): {e}")
                    if retry_count >= MAX_RETRIES:
                        print(f"Failed to upload {file_name} after {MAX_RETRIES} retries.")
                        break
                    time.sleep(5)

        if response:
            print(f"Upload complete for {file_name}")

    # Clean up the temporary file
    os.remove(temp_file_path)
    print(f"Temporary file {temp_file_path} deleted after upload.")

    # Record completion time and calculate elapsed time
    end_time = datetime.now()
    elapsed_time = end_time - start_time
    print(f"[{end_time}] Completed processing for: {file_name}")
    print(f"Total elapsed time: {elapsed_time}")


def main():
    start_time = datetime.now()  # Record the script's start time
    print(f"[{start_time}] Script started.")

    # Get the list of files from HyperDeck
    response = requests.get(HYPERDECK_URL)
    if response.status_code == 200:
        files = response.json()

        for file_info in files:
            file_name = file_info['name']
            file_url = HYPERDECK_URL + file_name
            upload_large_file(file_name, file_url)
    else:
        print("Failed to retrieve files from HyperDeck.")

    # Record the script's end time and calculate elapsed time
    end_time = datetime.now()
    elapsed_time = end_time - start_time
    print(f"[{end_time}] Script completed.")
    print(f"Total elapsed time for all files: {elapsed_time}")


if __name__ == "__main__":
    main()
