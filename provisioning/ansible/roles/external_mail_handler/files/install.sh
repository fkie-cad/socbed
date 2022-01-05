#! /bin/sh

# This script adds a command to /etc/rc.local so that external_mail_handler.py is executed on startup.
# Additionally it creates a logrotate config file for logs

SCRIPT="external_mail_handler.py"
SCRIPT_DIR="/usr/bin"
SERVICE_NAME="externalmailhandler"

SCRIPT_PATH="${SCRIPT_DIR}/${SCRIPT}"
EXEC_CMD="/usr/bin/python3 ${SCRIPT_PATH}"

# Copy the script to fixed destination
mkdir -p ${SCRIPT_DIR}
BASEDIR=$(dirname "$0")
cp "${BASEDIR}/${SCRIPT}" "${SCRIPT_PATH}"
echo "Copied ${SCRIPT} to ${SCRIPT_DIR}"

# Optionally prepare directory for logging
mkdir -p /var/log/breach
echo "Created log directory /var/log/breach"

# create logrotate config
cat <<EOM > /etc/logrotate.d/breach
/var/log/breach/external_mail_handler.log {
  daily
  rotate 365
  create
  missingok
  notifempty
}
EOM
echo "Created logrotate config /etc/logrotate.d/breach"

# install script as service
cat <<EOM > /etc/systemd/system/${SERVICE_NAME}.service
# Unit file for SOCBED External Mail Handler Service

[Unit]
Description=SOCBED External Mail Handler
After=network.target

[Service]
Type=simple
ExecStart=${EXEC_CMD}
Restart=always

[Install]
WantedBy=multi-user.target

EOM
chmod 664 /etc/systemd/system/${SERVICE_NAME}.service
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}.service
echo "Installed script as service ${SERVICE_NAME}"