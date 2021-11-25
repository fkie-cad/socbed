#!/usr/bin/env bash

###############################################################################
#
#
# INSTALL APACHE SERVER ON ATTACKER
#
#
###############################################################################

# again we need to check whether apache needs to be installed
echo -n "Hey, $USER, do you need to install apache? (Yes/No): "
read install_apache

if [ "$install_apache" == "Yes" ] || [ "$install_apache" == "yes" ];
then
    echo "Installing Apache: ..."
    # Make sure Apache is installed
    apt-get install apache2
    echo "Done. Nice Apache is installed!"
else
    echo "Skip Apache Installation."
fi

###############################################################################
#
#
# REMOVE OLD DIRECTORIES FROM ATTACKER
#
#
###############################################################################

# now we remove everything from name based virtual hosting that was created
echo -n "Shell I remove the directories created for name based VH? (Yes/No): "
read remove_directories

if [ "$remove_directories" == "Yes" ] || [ "$install_apache" == "yes" ];
then
    rm -rf /var/www/sitea/
    echo "Removed /var/www/sitea/"
    rm -rf /var/www/siteb/
    echo "Removed /var/www/siteb/"
    rm -rf /var/www/logs/
    echo "Removed /var/www/logs"
else
    echo "Skipped Cleaning Process of name based Virtual Hosting Script."
fi

###############################################################################
#
#
# DELETE THE OLD CONFIGURATION FOR NAME BASED VIRTUAL HOSTING
#
#
###############################################################################

echo "Delete old configuration file for name based VH"

# delete content of 000-default.conf for virtual hosting in sites-available
echo "Delete content of: /etc/apache2/sites-available/000-default.conf"
echo "" > /etc/apache2/sites-available/000-default.conf

# delete content of 000-default.conf for virtual hosting in sites-enabled
echo "Delete content of: /etc/apache2/sites-enabled/000-default.conf"
echo "" > /etc/apache2/sites-enabled/000-default.conf

# delete content of ports.conf
echo "Delete content of: /etc/apache2/ports.conf"
echo "" > /etc/apache2/ports.conf
echo "Done. Deleted old configuration file of name based VH"

###############################################################################
#
#
# START IP BASED VIRTUAL HOSTING CONFIGURATION.
# TAKEN FROM: https://httpd.apache.org/docs/current/vhosts/ip-based.html
#
###############################################################################

# create direcoties and files

echo "Create new directories for ip based VH"
mkdir /var/www/vhost.com/
echo "Directory created: /var/www/vhost.com/"
mkdir /var/www/vhost.com/logs
echo "Directory created: /var/www/vhost.com/logs/"

echo "To be sure touch needed logs in previous"
touch /var/www/vhost.com/logs/error_log
echo "Touched: /var/www/vhost.com/logs/error_log"
touch /var/www/vhost.com/logs/access_log
echo "Touched: /var/www/vhost.com/logs/access_log"

# write configuration file
echo "Now we need to bind another ip address to our NIC"

# write additional lines to nic config file
echo "Write additional IP to NIC interface"
echo "" >> /etc/network/interfaces
echo "auto eth0:1" >> /etc/network/interfaces
echo "iface eth0:1 inet static" >> /etc/network/interfaces
echo "\taddress 172.18.1.1" >> /etc/network/interfaces
echo "\tnetmask 255.255.0.0" >> /etc/network/interfaces

# restart settings to activate changes
echo "Restart Settings to activate changes"
ifdown eth0 && ifup eth0
ifup eth0:1

echo "Typing 'ifconfig' you should now see another aliased interface!"
sleep 2

# now setup the new virtual host configuration file
echo "Writing new configuration files for VH - Sites-Available"

# we could also link sites-available with sites-enabled but I do not
# like this solution that much

# first for sites-available
echo "<VirtualHost 172.18.1.1:80>" >> /etc/apache2/sites-available/000-default.conf
echo "    DocumentRoot /var/www/vhost.com" >> /etc/apache2/sites-available/000-default.conf
echo "    ErrorLog /var/www/vhost.com/logs/error_log" >> /etc/apache2/sites-available/000-default.conf
echo "</VirtualHost>" >> /etc/apache2/sites-available/000-default.conf

# second for sites-enabled
echo "Writing new configuration file for VH - Sites-Enabled"
echo "<VirtualHost 172.18.1.1:80>" >> /etc/apache2/sites-enabled/000-default.conf
echo "    DocumentRoot /var/www/vhost.com" >> /etc/apache2/sites-enabled/000-default.conf
echo "    ErrorLog /var/www/vhost.com/logs/error_log" >> /etc/apache2/sites-enabled/000-default.conf
echo "</VirtualHost>" >> /etc/apache2/sites-enabled/000-default.conf

# third we need to edit the ports.conf file
echo "Listen 172.18.1.1:80" >> /etc/apache2/ports.conf

echo ""
echo "With this configuration Apache should *only* be bound to 172.18.1.1"
echo "Doing to our handler can run on 172.18.0.3:80 and the Apache on 172.18.1.1:80"
echo ""

# finally we restart apache
echo "Now we need to restart Apache"
echo "You should also restart the machine itself to be sure."
echo "Made some bad experience on that ;D"

# again we need to check whether apache needs to be installed
echo -n "$USER, should I restart the machine? (Yes/No): "
read restart_machine

if [ "$restart_machine" == "Yes" ] || [ "$restart_machine" == "yes" ];
then
    echo "Do not forget to remove the redirection rule on the Client."
    echo "Check C:\Windows\System32\drivers\etc\hosts"
    echo "Delete line: '172.18.0.3 sitea.com'"
    sleep 2
    echo "Restarting Machine: ..."
    reboot
fi

echo "- Finished. Have FUN! - "

###############################################################################
#
#
# LAST STEPS TO BE DONE MANUALLY
# 
#
###############################################################################

echo "Do not forget to remove the redirection rule on the Client."
echo "Check C:\Windows\System32\drivers\etc\hosts"
echo "Delete line: '172.18.0.3 sitea.com'"
