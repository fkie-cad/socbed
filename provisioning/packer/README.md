This directory contains the Packer templates and configuration / provisioning files.

Commands
--------
Install Packer

```
$ packer build InternetRouter.json
$ packer build CompanyRouter.json
$ packer build logserver.json
$ packer build internalserver.json
$ packer build dmzserver.json
$ packer build Attacker.json
$ packer build client.json
```

JSON config templates
---------------------

JSON doesn't support comments. Refer https://www.packer.io/guides/workflow-tips-and-tricks/use-packer-with-comment.html if you want alternative workflows.
Packer introduced a new confguration format (.pkr.hcl) which can support comments in the beginning of 2020. Our json configs can be migrated to that format later, with additional comments explaining the configuration choices when it becomes the standardized workflow.

Pre-seeding
-----------

Ubuntu Guide: https://help.ubuntu.com/16.04/installation-guide/amd64/apb.html

Ubuntu Example Preseed: https://help.ubuntu.com/16.04/installation-guide/example-preseed.txt

Debian Example Preseed: https://www.debian.org/releases/sarge/example-preseed.txt

Gotchas
-------

Make sure that the preseed file is accessed using a IP address that'll be available after the static IP configuration takes place.

IPFire: CompanyRouter and InternetRouter
-------
Make sure that the subnet 192.168.56/24 is configured as HostOnlyAdapter vboxnet0 in VirtualBox.

Login to the VMs after installation with Packer with root/breach. The web-interface is availible after VM-login with admin/breach.

Web-Interface CompanyRouter: https://192.168.56.10:444/

Web-Interface InternetRouter: https://192.168.56.30:444/

Attention: You have to accept that there is no valid certificate for this site in your browser

No preseeding-file is needed.

Build InternetRouter before CompanyRouter (CR needs Internet from IR during building-process).


Attacker
-------------
The Attacker is based on kali-linux-2019.3-amd64. 

Access with 192.168.56.31 in your HostOnlyNetwork vboxnet0.

Login to the VM after installation with Packer with root/breach.
