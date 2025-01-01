#!/usr/bin/python3
import configparser
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import socket

# Load configuration
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.ini')
config = configparser.ConfigParser()
config.read(config_path)

# Get email settings from config
SMTP_SERVER = config.get('Email', 'SMTP_SERVER')
SMTP_PORT = config.getint('Email', 'SMTP_PORT')
SMTP_USERNAME = config.get('Email', 'SMTP_USERNAME')
SMTP_PASSWORD = config.get('Email', 'SMTP_PASSWORD')
RECIPIENT_EMAIL = config.get('Email', 'RECIPIENT_EMAIL')

# Create message
hostname = socket.gethostname()
subject = f"[{hostname}] ⚠️ Rocketpool Monitor Stopped"
message = f"Rocketpool monitor service stopped at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

# Send email
msg = MIMEMultipart()
msg['From'] = SMTP_USERNAME
msg['To'] = RECIPIENT_EMAIL
msg['Subject'] = subject
msg.attach(MIMEText(message, 'plain'))

with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    server.starttls()
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    server.send_message(msg)