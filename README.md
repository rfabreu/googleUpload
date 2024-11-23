# HyperDeck & Google Drive Upload Automation Tool

## Overview

This tool automates the process of downloading media files from a Blackmagic HyperDeck device, uploading them to a specified Google Drive folder, and sending email notifications upon task completion. It features an interactive command-line interface (CLI) that guides users through selecting files for processing and ensures seamless integration with HyperDeck and Google Drive.

---

## Features

- **Interactive CLI**: Prompts the user to configure the HyperDeck connection, select files, and define custom file names.
- **HyperDeck Integration**: Connects to HyperDeck devices, lists available folders and files for download.
- **File Upload to Google Drive**: Supports large file uploads with resumable upload sessions for reliability.
- **Email Notifications**: Sends a success notification to the configured email upon completion of file uploads.
- **Progress Tracking**: Provides a progress bar with real-time updates during downloads and uploads.

---

## Prerequisites

### Software Requirements
- Python 3.8 or later
- Required Python libraries:
  - `requests`
  - `tqdm`
  - `google-auth`
  - `google-api-python-client`
  - `python-dotenv`

### Setup
1. **Google Service Account**:
   - Create a Google Service Account with access to Google Drive.
   - Download the credentials JSON file for the service account.

2. **App Password for Email**:
   - Enable 2-Step Verification for your Gmail account.
   - Generate an App Password for SMTP access to Gmail.

3. **HyperDeck Device**:
   - Ensure the Blackmagic HyperDeck device is accessible via its IP or URL.

---

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/rfabreu/googleUpload.git
   cd googleUpload
   ```

2. Create a Python virtual environment and activate it:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scriptsctivate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up a `.env` file for environment variables (see below).

---

## Environment Variables

Create a `.env` file in the root directory with the following contents:

```env
SERVICE_ACCOUNT_FILE=/path/to/your/service_account.json
FOLDER_ID=your-google-drive-folder-id
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-app-password
EMAIL_TO=recipient-email@example.com
```

- `SERVICE_ACCOUNT_FILE`: Path to the Google Service Account credentials JSON file.
- `FOLDER_ID`: The ID of the Google Drive folder where files will be uploaded.
- `SMTP_USER`: Your Gmail address for sending notifications.
- `SMTP_PASSWORD`: The App Password for your Gmail account.
- `EMAIL_TO`: The recipient email address for notifications.

---

## Usage

1. Run the script:

   ```bash
   python googleUpload.py
   ```

2. Follow the interactive prompts:

   - **Enter the HyperDeck IP or URL**: Input the IP or URL of the HyperDeck device.
   - **Select Folder**: Choose a folder from the list of available folders.
   - **Select Files**: Specify the files to download and upload by entering their corresponding numbers.
   - **Set Custom Name**: Enter a custom name for the downloaded files (extensions will be preserved).

3. The tool will:
   - Download the selected files to a temporary location.
   - Upload the files to Google Drive with the specified name.
   - Send an email notification upon completion.

---

## Example Workflow

```plaintext
$ python googleUpload.py

Enter the HyperDeck IP or URL: 192.xxx.xx.xx
Connecting to HyperDeck at http://192.xxx.xx.xx/mounts/...

Available folders:
1. UNTITLED-sd1
2. UNTITLED-sd2

Select a folder by number: 1
Accessing folder: UNTITLED-sd1

Available files:
1. HyperDeck_0001.mcc
2. HyperDeck_0001.mov

Enter the file numbers to queue for download (comma-separated): 1,2
Enter a custom name for the downloaded files (without extension): CustomFileName

Starting download and upload for: HyperDeck_0001.mcc
Starting download for: HyperDeck_0001.mcc (Total Size: 10 MB)
Downloading HyperDeck_0001.mcc: 100%|█████████████████████| 10MB/10MB [00:05<00:00, 2MB/s]
Download complete for HyperDeck_0001.mcc.
Starting upload for CustomFileName.mcc...
Uploading CustomFileName.mcc: 100%|█████████████████████| 10MB/10MB [00:10<00:00, 1MB/s]
Upload complete for CustomFileName.mcc.

Email notification sent successfully.
```

---

## Troubleshooting

- **Email Notifications Failing**:
  - Ensure the `.env` file contains valid SMTP credentials (`SMTP_USER` and `SMTP_PASSWORD`).
  - Verify that the Gmail account has 2-Step Verification enabled and an App Password configured.

- **Connection to HyperDeck Failing**:
  - Ensure the HyperDeck IP/URL is correct and accessible from your network.

- **Upload Errors**:
  - Check the `FOLDER_ID` in the `.env` file to ensure it is valid and the Service Account has write permissions for the Google Drive folder.

---

## Contributing

Feel free to fork this repository and submit pull requests for improvements or bug fixes.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.
