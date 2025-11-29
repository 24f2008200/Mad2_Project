# backend/services/mail_utils.py
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv


load_dotenv()

# Gmail SMTP configuration
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER", "baskaran.nadar@gmail.com")
SMTP_PASS = os.environ.get("SMTP_PASS_PBN") 


def send_email(to_email, subject, html_body, attachments=None):
    """Send an HTML email with optional attachments."""
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    msg.set_content("This email contains HTML content.")
    msg.add_alternative(html_body, subtype='html')

    # Optional file attachments
    if attachments:
        for filename, content, mime in attachments:
            maintype, subtype = mime.split('/')
            msg.add_attachment(
                content, maintype=maintype, subtype=subtype, filename=filename
            )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)
