#!/usr/bin/env bash

echo "4,ACCEPT,FORWARDFW,ON,std_net_src,ALL,tgt_addr,172.17.0.2/32,,TCP,,,ON,,,cust_srv,SMTP,Port Forwarding for SMTP to Mailserver,ON,,,,,,,,,00:00,00:00,ON,Default IP,25,dnat,,,,,second" >> /var/ipfire/firewall/config
echo "3,ACCEPT,FORWARDFW,ON,std_net_src,ORANGE,std_net_tgt,GREEN,,TCP,,,ON,,,cust_srv,Wazuh Registration,Allow Wazuh Registration,,,,,,,,,,00:00,00:00,,AUTO,,dnat,,,,,second" >> /var/ipfire/firewall/config
echo "2,ACCEPT,FORWARDFW,ON,std_net_src,ORANGE,std_net_tgt,GREEN,,TCP,,,ON,,,cust_srv,Wazuh Communication,Allow Wazuh Communication,,,,,,,,,,00:00,00:00,,AUTO,,dnat,,,,,second" >> /var/ipfire/firewall/config
echo "1,ACCEPT,FORWARDFW,ON,std_net_src,ORANGE,std_net_tgt,GREEN,,TCP,,,ON,,,cust_srv,syslog (tcp),Allow syslog TCP on port 514 from ORANGE to GREEN,,,,,,,,,,00:00,00:00,,AUTO,,dnat,,,,,second" >> /var/ipfire/firewall/config
echo "6,ACCEPT,FORWARDFW,ON,std_net_src,ALL,tgt_addr,172.17.0.2/32,,TCP,,,ON,,,cust_srv,HTTP,Port Forwarding for HTTP to Webserver,ON,,,,,,,,,00:00,00:00,ON,Default IP,80,dnat,,,,,second" >> /var/ipfire/firewall/config
echo "5,ACCEPT,FORWARDFW,ON,std_net_src,ALL,tgt_addr,172.17.0.2/32,,TCP,,,ON,,,cust_srv,Submission (TCP),Port Forwarding for SMTP to Mailserver,ON,,,,,,,,,00:00,00:00,ON,Default IP,587,dnat,,,,,second" >> /var/ipfire/firewall/config

sed -i '8iiptables -I INPUT -p tcp --dport 222 -j ACCEPT' /etc/sysconfig/firewall.local
sed -i '9iiptables -I INPUT -p tcp --dport 444 -j ACCEPT' /etc/sysconfig/firewall.local

echo "3,172.18.0.1,,enabled," > /var/ipfire/dns/servers
echo "USP_ISP_NAMESERVERS=off" > /var/ipfire/dns/settings
echo "QNAME_MIN=standard" >> /var/ipfire/dns/settings
echo "PROTO=UDP" >> /var/ipfire/dns/settings
echo "ENABLE_SAFE_SEARCH=off" >> /var/ipfire/dns/settings

/etc/init.d/unbound restart

pakfire update
pakfire install python3-setuptools -y
