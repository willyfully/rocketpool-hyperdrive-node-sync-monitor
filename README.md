# Rocketpool/Hyperdrive Node Sync Monitor
## Overview
This script monitors Rocketpool and Hyperdrive nodes clients sync status.
It sends an email at startup with a full report of all clients sync status.
It then checks every 5 minutes the clients sync status and sends an email when a client sync status changes. The email details all sync status changes plus a recap of all clients that are not synced.
It sends an email with a full report of all clients sync status every day at 00:00.
The service sends an email if the service stops.

The script runs the rocketpool node sync or hyperdrive service sync commands and parses the output to check if the node is synced.

## Installation:
1. This script uses mailx to send emails. Install and test mailx on your system if it is not already installed.
2. Create the installation directory and copy files:
   ```bash
   sudo mkdir -p /opt/rocketpool_monitor
   sudo cp rocketpool_monitor.py send_stop_notification.py config.template.ini /opt/rocketpool_monitor/
   ```
3. Copy and configure the settings (see details below):
   ```bash
   sudo cp /opt/rocketpool_monitor/config.template.ini /opt/rocketpool_monitor/config.ini
   sudo nano /opt/rocketpool_monitor/config.ini
   ```
4. Copy the service file:
   ```bash
   sudo cp rocketpool_monitor.service /etc/systemd/system/
   ```
5. Reload systemd: sudo systemctl daemon-reload
6. Enable the service to start at boot: sudo systemctl enable rocketpool_monitor
7. Start the service: sudo systemctl start rocketpool_monitor
8. Check status: sudo systemctl status rocketpool_monitor
9. View logs: sudo journalctl -u rocketpool_monitor -f or: sudo journalctl -u rocketpool_monitor

The script can also be run manually with:
/usr/bin/python3 /opt/rocketpool_monitor/rocketpool_monitor.py --log-level INFO
Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Configuration
In `config.ini` (copy of `config.template.ini`) edit the following settings:

### Email Settings
- SMTP_SERVER: Your email server address
- SMTP_PORT: Email server port (usually 587 for TLS)
- SMTP_USERNAME: Your email username
- SMTP_PASSWORD: Your email password or app-specific password
- RECIPIENT_EMAIL: Where to send monitoring emails

### Paths
- ROCKETPOOL_BIN: Path to rocketpool binary (e.g., /home/USER/bin/rocketpool)
- HYPERDRIVE_BIN: Path to hyperdrive binary (e.g., /usr/bin/hyperdrive)

### Nodes Configuration
In the [Nodes] section, each line defines a node to monitor:
```ini
node_name = type,data_dir
```
- node_name: Name to identify the node in notifications
- type: Either 'rocketpool' or 'hyperdrive'
- data_dir: Path to the node's data directory

Example:
```ini
rp1 = rocketpool,/home/USER/.rocketpool
rp2 = rocketpool,/home/USER/.rocketpool2
rp3 = rocketpool,/home/USER/.rocketpool3
hyperdrive = hyperdrive,/home/USER/.hyperdrive
```

### Monitor Settings
- CHECK_INTERVAL: Time between checks in seconds (default: 300)
- DAILY_REPORT_TIME: Time for daily report (format: "HH:MM")

Note: The `config.ini` file is ignored by git to keep your private information secure. Never commit your actual config.ini file to the repository.


