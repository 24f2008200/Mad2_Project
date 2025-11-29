# backend/tasks/chat_utils.py
import os ,sys
import requests
from flask import current_app
from dotenv import load_dotenv

default_google_chat_webhook = os.getenv("GOOGLE_CHAT_HOOK" ,"")


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
