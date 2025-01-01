import configparser
import os

# Load configuration
config = configparser.ConfigParser()
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.ini')
print(script_dir)
print(config_path)
if not os.path.exists(config_path):
    raise FileNotFoundError(f"Configuration file not found at {config_path}. Please copy config.template.ini to config.ini and edit it.")
config.read(config_path)

# Replace the hardcoded paths with config values
ROCKETPOOL_BIN = config.get('Paths', 'ROCKETPOOL_BIN')
HYPERDRIVE_BIN = config.get('Paths', 'HYPERDRIVE_BIN')
ROCKETPOOL_DATA_DIR = config.get('Paths', 'ROCKETPOOL_DATA_DIR')
ROCKETPOOL_DATA_DIR2 = config.get('Paths', 'ROCKETPOOL_DATA_DIR2')
ROCKETPOOL_DATA_DIR3 = config.get('Paths', 'ROCKETPOOL_DATA_DIR3')
HYPERDRIVE_DATA_DIR = config.get('Paths', 'HYPERDRIVE_DATA_DIR')

# Get other configuration values
CHECK_INTERVAL = config.getint('Monitor', 'CHECK_INTERVAL')
DAILY_REPORT_TIME = config.get('Monitor', 'DAILY_REPORT_TIME')

# Email settings
SMTP_SERVER = config.get('Email', 'SMTP_SERVER')
SMTP_PORT = config.getint('Email', 'SMTP_PORT')
SMTP_USERNAME = config.get('Email', 'SMTP_USERNAME')
SMTP_PASSWORD = config.get('Email', 'SMTP_PASSWORD')
RECIPIENT_EMAIL = config.get('Email', 'RECIPIENT_EMAIL')

import subprocess
from datetime import datetime
import time
import socket
import logging
import logging.handlers
import os
import argparse

class RocketpoolMonitor:
    def __init__(self, rp_configs, email_config, log_level='INFO'):
        # Set up logging
        self.logger = logging.getLogger('RocketpoolMonitor')
        self.logger.setLevel(getattr(logging, log_level))
        
        # Clear any existing handlers
        self.logger.handlers = []
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        
        # Add handlers based on how we're running
        if os.environ.get('JOURNAL_STREAM'):  # Running as a service
            # Only use SysLogHandler when running as a service
            syslog_handler = logging.handlers.SysLogHandler(address='/dev/log')
            syslog_handler.setFormatter(formatter)
            self.logger.addHandler(syslog_handler)
        else:  # Running manually
            # Only use StreamHandler when running manually
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        self.rp_configs = rp_configs
        self.email_config = email_config
        self.sync_issues = {}
        self.last_summary_day = None
        self.current_messages = []
        
        # Initialize sync status for all clients
        for rp_config in rp_configs:
            sync_output = self.run_command(rp_config, "node sync")
            if "Error" not in sync_output:
                statuses = self.parse_sync_status(sync_output)
                for client_type, is_synced in statuses.items():
                    key = f"{rp_config['alias']}:{client_type}"
                    self.sync_issues[key] = is_synced

    def send_email(self, subject, message):
        """Send email using smtplib with external SMTP server"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            hostname = socket.gethostname()
            subject_with_host = f"[{hostname}] {subject}"
            
            # Log email content
            self.logger.info(f"Sending email:\nSubject: {subject_with_host}\nContent:\n{message}")
            
            # Create MIME message
            msg = MIMEMultipart()
            msg['From'] = SMTP_USERNAME
            msg['To'] = RECIPIENT_EMAIL
            msg['Subject'] = subject_with_host
            msg.attach(MIMEText(message, 'plain'))
            
            # Connect to SMTP server
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
            
            self.logger.info("Email sent successfully")
            
        except Exception as e:
            self.logger.error(f"Error sending email: {str(e)}")

    def log_and_notify(self, message, is_alert=False):
        """Queue message for batch sending"""
        self.logger.info(message)
        if is_alert or "=== Daily Summary" in message:
            self.current_messages.append(message)

    def run_command(self, rp_config, command):
        """Run a rocketpool command"""
        try:
            # For backward compatibility, but we only use the command from config now
            full_command = rp_config['command']
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr.strip()}"
        except Exception as e:
            return f"Error: {str(e)}"

    def parse_sync_status(self, output):
        """Parse the sync status output and return a dictionary of client statuses"""
        client_statuses = {
            'primary_execution': False,
            'fallback_execution': False,
            'primary_consensus': False,
            'fallback_consensus': False
        }
        
        # Note: Rocketpool uses "consensus client" terminology while Hyperdrive uses "beacon client"
        # Both mean the same thing, so we check for both in the output
        for line in output.split('\n'):
            line = line.lower().strip()
            if "primary execution client is fully synced" in line:
                client_statuses['primary_execution'] = True
            elif "fallback execution client is fully synced" in line:
                client_statuses['fallback_execution'] = True
            elif "primary consensus client is fully synced" in line or "primary beacon client is fully synced" in line:
                client_statuses['primary_consensus'] = True
            elif "fallback consensus client is fully synced" in line or "fallback beacon client is fully synced" in line:
                client_statuses['fallback_consensus'] = True
        
        return client_statuses

    def check_node_sync(self, rp_config):
        """Check sync status for a specific rocketpool node and report changes"""
        sync_output = self.run_command(rp_config, "node sync")
        
        if "Error" in sync_output:
            message = f"⚠️  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Failed to get sync status for {rp_config['alias']}: {sync_output}"
            self.log_and_notify(message, is_alert=True)
            return
        
        statuses = self.parse_sync_status(sync_output)
        
        # Check each client's status and alert on changes
        for client_type, is_synced in statuses.items():
            key = f"{rp_config['alias']}:{client_type}"
            prev_status = self.sync_issues.get(key, True)
            
            if not is_synced and prev_status:
                message = f"⚠️  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {rp_config['alias']}: {client_type.replace('_', ' ').title()} is not synced!"
                self.log_and_notify(message, is_alert=True)
                self.sync_issues[key] = False
            elif is_synced and not prev_status:
                message = f"✓ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {rp_config['alias']}: {client_type.replace('_', ' ').title()} is back in sync"
                self.log_and_notify(message, is_alert=True)
                self.sync_issues[key] = True

    def get_status_summary(self):
        """Get a summary of all nodes' status"""
        summary_lines = []
        
        for rp_config in self.rp_configs:
            summary_lines.append(f"\n{rp_config['alias']} Status:")
            sync_output = self.run_command(rp_config, "node sync")
            
            if "Error" in sync_output:
                summary_lines.append(f"⚠️  Failed to get status")
                continue
            
            statuses = self.parse_sync_status(sync_output)
            for client_type, is_synced in statuses.items():
                status_symbol = "✓" if is_synced else "⚠️ "
                status_text = "synced" if is_synced else "not synced"
                summary_lines.append(f"{status_symbol} {client_type.replace('_', ' ').title()}: {status_text}")
        
        return "\n".join(summary_lines)

    def print_daily_summary(self):
        """Print a summary of all clients' status"""
        summary = f"\n=== Daily Summary ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===" + self.get_status_summary()
        self.log_and_notify(summary)

    def check_all_nodes(self):
        """Check all rocketpool nodes and send batch notification"""
        self.current_messages = []
        status_changed = False
        all_current_statuses = {}
        
        current_time = datetime.now()
        current_day = current_time.date()
        
        if self.last_summary_day != current_day and current_time.hour == 0 and current_time.minute < 5:
            self.print_daily_summary()
            self.last_summary_day = current_day
        
        self.logger.debug("Current sync_issues state:")
        for key, value in self.sync_issues.items():
            self.logger.debug(f"{key}: {value}")
        
        # First check all nodes and collect status changes
        for rp_config in self.rp_configs:
            sync_output = self.run_command(rp_config, "node sync")
            
            if "Error" in sync_output:
                message = f"⚠️  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Failed to get sync status for {rp_config['alias']}: {sync_output}"
                self.log_and_notify(message, is_alert=True)
                continue
            
            statuses = self.parse_sync_status(sync_output)
            self.logger.debug(f"{rp_config['alias']} current statuses:")
            self.logger.debug(statuses)
            
            # Check each client's status and alert on changes
            for client_type, is_synced in statuses.items():
                key = f"{rp_config['alias']}:{client_type}"
                all_current_statuses[key] = is_synced
                prev_status = self.sync_issues.get(key, True)
                
                self.logger.debug(f"Checking {key}:")
                self.logger.debug(f"Previous status: {prev_status}")
                self.logger.debug(f"Current status: {is_synced}")
                
                if not is_synced and prev_status:
                    self.logger.debug("Detected not synced change")
                    message = f"⚠️  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {rp_config['alias']}: {client_type.replace('_', ' ').title()} is not synced!"
                    self.log_and_notify(message, is_alert=True)
                    status_changed = True
                elif is_synced and not prev_status:
                    self.logger.debug("Detected back in sync change")
                    message = f"✓ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {rp_config['alias']}: {client_type.replace('_', ' ').title()} is back in sync"
                    self.log_and_notify(message, is_alert=True)
                    status_changed = True
                
                self.sync_issues[key] = is_synced

        self.logger.debug(f"Status changed: {status_changed}")
        self.logger.debug("All current statuses:")
        for key, value in all_current_statuses.items():
            self.logger.debug(f"{key}: {value}")

        # If any status changed, add a recap of all not synced clients
        if status_changed:
            not_synced = []
            for key, is_synced in all_current_statuses.items():
                if not is_synced:
                    node, client = key.split(':')
                    not_synced.append(f"  • {node}: {client.replace('_', ' ').title()}")
            
            print("\nDebug - Not synced clients:")
            print(not_synced)
            
            if not_synced:
                recap = f"\nCurrently not synced clients:\n" + "\n".join(sorted(not_synced))
                self.log_and_notify(recap, is_alert=True)

        # Send all collected messages in one email
        if self.current_messages:
            subject = "🚨 Rocketpool Status Update"
            message = "\n".join(self.current_messages)
            self.send_email(subject, message)

if __name__ == "__main__":
    # Add command line argument parsing
    parser = argparse.ArgumentParser(description='Monitor Rocketpool nodes sync status')
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set the logging level (default: INFO)'
    )
    args = parser.parse_args()
    
    # Email configuration
    email_config = {
        'to': RECIPIENT_EMAIL
    }
    
    # Rocketpool configuration
    rp_configs = [
        {
            'alias': 'rp1',
            'command': f'{ROCKETPOOL_BIN} --allow-root -c {ROCKETPOOL_DATA_DIR} node sync'
        },
        {
            'alias': 'rp2',
            'command': f'{ROCKETPOOL_BIN} --allow-root -c {ROCKETPOOL_DATA_DIR2} node sync'
        },
        {
            'alias': 'rp3',
            'command': f'{ROCKETPOOL_BIN} --allow-root -c {ROCKETPOOL_DATA_DIR3} node sync'
        },
        {
            'alias': 'hyperdrive',
            'command': f'{HYPERDRIVE_BIN} --allow-root -c {HYPERDRIVE_DATA_DIR} service sync'
        }
    ]
    
    monitor = RocketpoolMonitor(rp_configs, email_config, args.log_level)
    
    # Send startup message with initial status
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    start_message = f"Starting Rocketpool monitor at {start_time}\nMonitoring for sync issues...\n\n=== Initial Status ==={monitor.get_status_summary()}"
    monitor.send_email("🚀 Rocketpool Monitor Starting", start_message)
    
    while True:
        start_time = datetime.now()
        monitor.check_all_nodes()
        
        # Calculate time until next check interval
        current_time = datetime.now()
        minutes_to_next = CHECK_INTERVAL/60 - (current_time.minute % (CHECK_INTERVAL/60))
        seconds_to_next = minutes_to_next * 60 - current_time.second
        
        # If we're very close to the next interval, add one full interval
        if seconds_to_next < 10:
            seconds_to_next += CHECK_INTERVAL
            
        monitor.logger.info(f"Next check in {seconds_to_next} seconds")
        time.sleep(seconds_to_next)