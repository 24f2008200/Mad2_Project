import os
import smtplib
from email.message import EmailMessage
from backend.tasks.chat_utils import send_google_chat
from dotenv import load_dotenv


load_dotenv()

# Gmail SMTP configuration
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER", "baskaran.nadar@gmail.com")
SMTP_PASS = os.environ.get("SMTP_PASS_PBN")  # <- paste your app password here for testing

def send_email(to_email, subject, html_body, attachments=None):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    msg.set_content("This email contains HTML. Please open it in an HTML-capable client.")
    msg.add_alternative(html_body, subtype='html')

    if attachments:
        for filename, content, mime in attachments:
            maintype, subtype = mime.split('/')
            msg.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)
        print(" Email sent successfully to", to_email)


# --- Test it ---
if __name__ == "__main__":
    html = """
    <html>
        <body>
            <h2>Hello from Mars 👽</h2>
            <p>This is a 4th test email sent from Python using Gmail SMTP.</p>
        </body>
    </html>
    """
    send_email("dad@makshi.in", "Test Email from Flask", html)
    send_google_chat(text="Test message from mail_utils.py")
