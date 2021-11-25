#!/usr/bin/env bash

echo "1,ACCEPT,FORWARDFW,ON,std_net_src,GREEN,std_net_tgt,RED,,TCP,,,ON,,,cust_srv,HTTP,Allow HTTP traffic from GREEN to RED,ON,,,,,,,,,00:00,00:00,,AUTO,,dnat,,,,,second" >> /var/ipfire/firewall/config
echo "2,ACCEPT,FORWARDFW,ON,std_net_src,GREEN,std_net_tgt,RED,,TCP,,,ON,,,cust_srv,HTTPS,Allow HTTPS traffic from GREEN to RED,ON,,,,,,,,,00:00,00:00,,AUTO,,dnat,,,,,second" >> /var/ipfire/firewall/config
echo "3,ACCEPT,FORWARDFW,ON,std_net_src,GREEN,std_net_tgt,RED,,UDP,,,ON,,,cust_srv,NTP,,ON,,,,,,,,,00:00,00:00,,AUTO,,dnat,,,,,second" >> /var/ipfire/firewall/config

sed -i '8iiptables -I INPUT -p tcp --dport 222 -j ACCEPT' /etc/sysconfig/firewall.local
sed -i '9iiptables -I INPUT -p tcp --dport 444 -j ACCEPT' /etc/sysconfig/firewall.local

echo "USP_ISP_NAMESERVERS=off" > /var/ipfire/dns/settings
echo "QNAME_MIN=standard" >> /var/ipfire/dns/settings
echo "PROTO=UDP" >> /var/ipfire/dns/settings
echo "ENABLE_SAFE_SEARCH=off" >> /var/ipfire/dns/settings

/etc/init.d/unbound restart

pakfire update
pakfire install python3-setuptools -y
