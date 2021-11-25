#!/usr/bin/env bash

sudo sed -i "s/PermitRootLogin prohibit-password/PermitRootLogin yes/g" /etc/ssh/sshd_config
sudo systemctl restart sshd.service
sudo mv /etc/network/interfaces /etc/network/interfaces.old
sudo bash -c 'cat > /etc/network/interfaces' <<EOF
source /etc/network/interfaces.d/*

auto lo
iface lo inet loopback

auto enp0s3
     iface enp0s3 inet static
     address 172.16.0.2
     netmask 255.255.0.0
     network 172.16.0.0
     broadcast 172.16.255.255
     gateway 172.16.0.1
     dns-nameservers 172.16.0.1
     dns-search breach.local

auto enp0s8
iface enp0s8 inet static
      address 192.168.56.11
      netmask 255.255.255.0

EOF

sudo ip addr flush enp0s8 && systemctl restart networking.service
sudo reboot

