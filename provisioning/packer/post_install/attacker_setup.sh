#!/usr/bin/env bash

# Enable root account, set password and reboot
touch /tmp/runasroot.sh

echo "apt update" > /tmp/runasroot.sh
echo "apt install kali-root-login" >> /tmp/runasroot.sh
echo "echo 'root:breach' | chpasswd" >> /tmp/runasroot.sh
echo "reboot" >> /tmp/runasroot.sh

echo breach | sudo -S chmod +x /tmp/runasroot.sh
echo breach | sudo -S /tmp/runasroot.sh

