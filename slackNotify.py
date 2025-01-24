import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SLACK_USERNAME = os.getenv("SLACK_USERNAME")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")


def send_notification(message):
    """
    Sends a notification to Slack using the configured webhook URL.
    :param message: The message to send to Slack.
    """
    if not SLACK_WEBHOOK_URL:
        print("Slack webhook URL is not configured. Skipping Slack notification.")
        return

    payload = {
        "username": SLACK_USERNAME,
        "channel": SLACK_CHANNEL,
        "text": message,
    }

    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print("Slack notification sent successfully.")
        else:
            print(f"Failed to send Slack notification. Status code: {response.status_code}")
            print("Response:", response.text)
    except Exception as e:
        print(f"Error sending Slack notification: {e}")