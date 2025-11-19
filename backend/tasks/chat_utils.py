# backend/tasks/chat_utils.py
import requests
from flask import current_app

default_google_chat_webhook = "https://chat.googleapis.com/v1/spaces/AAQAwtQ63ag/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=5MYSUrPN6reLnOlxNcejvgkOJ35PtxS2QRY6c_FTM7c"


def send_google_chat(text ,webhook_url = default_google_chat_webhook):
    """Send a message to a Google Chat space using webhook."""
    payload = {"text": text}
    try:
        requests.post(webhook_url, json=payload, timeout=5)
    except Exception as e:
        if current_app:
            current_app.logger.exception("Failed to send Google Chat message: %s", e)
        else:
            print(f"Google Chat send failed: {e}")
