# Rocketpool/Hyperdrive Node Sync Monitor
## Overview
This script monitors Rocketpool and Hyperdrive nodes clients sync status.
It sends an email at startup with a full report of all clients sync status.
It then checks every 5 minutes the clients sync status and sends an email when a client sync status changes. The email details all sync status changes plus a recap of all clients that are not synced.
It sends an email with a full report of all clients sync status every day at 00:00.
The service sends an email if the service stops.

The script runs the rocketpool node sync or hyperdrive service sync commands and parses the output to check if the node is synced.

## Credits
Special thanks to Cursor and Claude 3.5 Sonnet AI assistant for their invaluable contributions!

## Installation:
1. Create the installation directory and copy files:
   ```bash
   sudo mkdir -p /opt/rocketpool_monitor
   sudo cp rocketpool_monitor.py send_stop_notification.py config.template.ini /opt/rocketpool_monitor/
   ```
2. Copy the config file template and configure the settings (see details below):
   ```bash
   sudo cp /opt/rocketpool_monitor/config.template.ini /opt/rocketpool_monitor/config.ini
   sudo nano /opt/rocketpool_monitor/config.ini
   ```
3. Copy the service file:
   ```bash
   sudo cp rocketpool_monitor.service /etc/systemd/system/
   ```
4. Reload systemd:
   ```bash
   sudo systemctl daemon-reload
   ```
5. Enable the service to start at boot:
   ```bash
   sudo systemctl enable rocketpool_monitor
   ```
6. Start the service:
   ```bash
   sudo systemctl start rocketpool_monitor
   ```
## Configuration
In `config.ini` (copy of `config.template.ini`) edit the settings:

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

### Monitoring Settings
- CHECK_INTERVAL: Time between checks in seconds (default: 300)
- DAILY_REPORT_TIME: Time for daily report (format: "HH:MM")

Note: The `config.ini` file is ignored by git to keep your private information secure. Never commit your actual config.ini file to the repository.

## Maintenance
Check service status:
   ```bash
   sudo systemctl status rocketpool_monitor
   ```
View service logs:
   ```bash
   # Follow logs in real-time
   sudo journalctl -u rocketpool_monitor -f
   
   # View all logs
   sudo journalctl -u rocketpool_monitor
   ```
Run script manually:
```bash
sudo /usr/bin/python3 /opt/rocketpool_monitor/rocketpool_monitor.py --log-level INFO
```
Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`



