import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    config = {
        "sender_email": os.environ.get("SENDER_EMAIL", ""),
        "sender_password": os.environ.get("SENDER_PASSWORD") or os.environ.get("GMAIL_APP_PASSWORD", ""),
        "recipient_email": os.environ.get("RECIPIENT_EMAIL", ""),
        "smtp_host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": int(os.environ.get("SMTP_PORT", 587))
    }
    
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                file_config = json.load(f)
                for k, v in file_config.items():
                    if v and not config.get(k):
                        config[k] = v
        except Exception as e:
            print(f"[CONFIG WARNING] Could not read {CONFIG_PATH}: {e}")
            
    return config

def parse_recipients(recipient_input):
    if isinstance(recipient_input, list):
        return [r.strip() for r in recipient_input if isinstance(r, str) and r.strip()]
    if isinstance(recipient_input, str):
        return [r.strip() for r in recipient_input.split(",") if r.strip()]
    return []

from email.mime.application import MIMEApplication
import re

def send_weekly_email(subject, html_content, text_content, recipient_override=None, attachment_path=None):
    cfg = load_config()
    sender = cfg.get("sender_email", "")
    if isinstance(sender, str):
        sender = sender.strip()
    password = cfg.get("sender_password", "")
    if isinstance(password, str):
        password = password.strip()
        
    raw_recipient = recipient_override or cfg.get("recipient_email", "")
    recipients = parse_recipients(raw_recipient)
    
    smtp_host = cfg.get("smtp_host", "smtp.gmail.com")
    smtp_port = cfg.get("smtp_port", 587)

    if not sender or not password or not recipients:
        msg = f"[EMAIL DISPATCH] Email not sent because SMTP credentials or recipient email are not fully configured.\n" \
              f"Sender: {'SET' if sender else 'MISSING'}, Password: {'SET' if password else 'MISSING'}, Recipients: {len(recipients)} configured.\n" \
              f"Please update du_5th_grade_agent/config.json with your details."
        print(msg)
        return False, msg

    # Email clients (Gmail, Outlook, Yahoo) strip JavaScript onclick="window.print()" buttons.
    # Cleanly remove the button from the email HTML body.
    clean_html = re.sub(
        r'<button class="print-btn no-print"[^>]*>.*?</button>',
        '',
        html_content,
        flags=re.DOTALL
    )

    recipients_str = ", ".join(recipients)
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = f"DU Homework Agent <{sender}>"
    msg["To"] = recipients_str

    # Create alternative container for text + html
    body_part = MIMEMultipart("alternative")
    body_part.attach(MIMEText(text_content, "plain"))
    body_part.attach(MIMEText(clean_html, "html"))
    msg.attach(body_part)

    # Attach files if provided and exist
    attachments = attachment_path if isinstance(attachment_path, list) else ([attachment_path] if attachment_path else [])
    for att in attachments:
        if att and os.path.exists(att):
            try:
                with open(att, "rb") as f:
                    fname = os.path.basename(att)
                    part = MIMEApplication(f.read(), Name=fname)
                    part['Content-Disposition'] = f'attachment; filename="{fname}"'
                    msg.attach(part)
                    print(f"[EMAIL DISPATCH] Attached file '{fname}' to weekly email.")
            except Exception as ea:
                print(f"[EMAIL WARNING] Could not attach file {att}: {ea}")

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                server.login(sender, password)
                server.sendmail(sender, recipients, msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(sender, password)
                server.sendmail(sender, recipients, msg.as_string())

        success_msg = f"Email sent successfully to {recipients_str} via {smtp_host}:{smtp_port}!"
        print(f"[EMAIL SUCCESS] {success_msg}")
        return True, success_msg

    except Exception as e:
        err_msg = f"Failed to send email: {e}"
        print(f"[EMAIL ERROR] {err_msg}")
        return False, err_msg


