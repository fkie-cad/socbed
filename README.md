[![socbed build status](https://github.com/fkie-cad/socbed/actions/workflows/socbed-unittest.yml/badge.svg?branch=main)](https://github.com/fkie-cad/socbed/actions/workflows/socbed-unittest.yml?query=branch%3Amain)
[![socbed build status](https://github.com/fkie-cad/socbed/actions/workflows/socbed-systemtest.yml/badge.svg?branch=main)](https://github.com/fkie-cad/socbed/actions/workflows/socbed-systemtest.yml?query=branch%3Amain)

# SOCBED

SOCBED is a self-contained open-source cyberattack experimentation testbed that simulates a small company's network including benign user behavior, various cyber attacks, and a central collection of log data.

## Motivation

Use cases of SOCBED include research and training in the following areas: security incident response, digital forensics, log management, intrusion detection, and awareness.
The testbed can also be used to generate realistic log/traffic datasets for product or method evaluations.

## System Requirements

* Physical host with Linux or macOS (running VirtualBox in a virtual machine might be possible as well but was not tested)
* RAM: 16 GB minimum, 32 GB recommended
* CPU: Quad-core with hardware support for virtualization
* HDD: 50 GB free, SSD is mandatory

More resources are required depending on the desired number of simulated clients.
The numbers above are valid for small simulations with 1-10 clients.

## Installation

Installation instructions for SOCBED on a fresh *Ubuntu 20.04.2.0 LTS* system:

```sh
# Install VirtualBox and configure the management network interface
sudo apt install virtualbox virtualbox-ext-pack
vboxmanage hostonlyif create # should create vboxnet0, else adapt following lines
vboxmanage hostonlyif ipconfig vboxnet0 --ip 192.168.56.1 --netmask 255.255.255.0
vboxmanage dhcpserver modify --ifname vboxnet0 --disable

# Install packer v1.6.3
export VER="1.6.3"
sudo wget https://releases.hashicorp.com/packer/${VER}/packer_${VER}_linux_amd64.zip
sudo unzip packer_${VER}_linux_amd64.zip -d /usr/local/bin

# Install requirements for the python package "cryptography",
# see https://cryptography.io/en/latest/installation/
sudo apt install build-essential libssl-dev libffi-dev python3-dev

# Optional: Install packages for 1337 "message of the day" banner in the attackconsole
sudo apt install cowsay fortunes

# Create and activate a Python Virtual Environment
sudo apt install virtualenv
virtualenv -p python3 ~/.virtualenvs/socbed
source ~/.virtualenvs/socbed/bin/activate

# Download and install SOCBED in the virtual environment
git clone git@github.com:fkie-cad/socbed.git
cd socbed/
pip install -r requirements.txt
pip install --editable .
```

Next, build all SOCBED virtual machines via ansible and packer while within the virtual environment. Before doing so, you need to:
- Download a Windows 10 64-bit ISO image from Microsoft and place it in the `provisioning/packer/` directory. We are currently using version 21H2 (November 2021) in English for testing, but other versions should work as well.
- Change permissions with:
    ```sh
    sudo chmod 744 ./provisioning/packer/<filename>.iso
    ```
- Calculate the md5 checksum:
    ```sh
    md5sum ./provisioning/packer/<filename>.iso
    ```
- Update the `iso_url` and `iso_checksum` values in `provisioning/packer/client.json` accordingly.

The script below will execute everything required to build and configure each respective machine, including snapshotting.
It will download the remaining ISO files, automatically boot the machines and provision the necessary versions of software dependencies with no human interaction needed.
Be aware that this will take multiple (3-5) hours to complete, depending on your hardware and Internet speed.

```sh
# Current directory must be root directory of the SOCBED repository
./tools/build_vms
```
In case of an error, simply restart the script, it will recognize previously built machines and continue where it left off.
Note that the order in which the machines are built is not arbitrary, and deleting and rebuilding e.g. the Log Server after all machines have been built will result in loss of critical functionality.

After these steps, you can run the commands `vmconsole`, `attackconsole`, or `generateattackchains` within the virtual environment and work with the framework (see example below).
When finished, you can leave the virtual environment with the command
```sh
deactivate
```

## Testing

Install tox and pytest in your virtual environment if you haven't done it yet:
```sh
source ~/.virtualenvs/socbed/bin/activate # Activate virtual environment
pip install -r requirements.txt
```

Run all unit tests from the repository root directory:
```sh
tox -- -m "not systest"
```

If they succeed, run the essential system tests:
```sh
tox -- -m "systest and not longtest"
```

Attention: System tests will start and stop the virtual machines several times and  can take a while to complete!

## Example

This example shows how to run some attacks when the framework was installed as described above.

```sh
# Activate virtual environment
source ~/.virtualenvs/socbed/bin/activate

# Start the virtual machines
vmconsole -c start_session

# Start the attackconsole and run some commands
attackconsole
attackconsole > help
attackconsole > ls
attackconsole > use infect_email_exe
attackconsole (infect_email_exe) > options
attackconsole (infect_email_exe) > set addr client2@localdomain
attackconsole (infect_email_exe) > run
attackconsole (infect_email_exe) > back
attackconsole > use c2_change_wallpaper
attackconsole (c2_change_wallpaper) > run
attackconsole (c2_change_wallpaper) > back
attackconsole > exit

# Close and restore the virtual machines
vmconsole -c close_session

# Deactivate virtual environment
deactivate
```

## Cleaning up failed sessions

In case sessions crash for some reason, you might end up with several Client clones and several automatically generated snapshots named `Backup*`.
To clean up the mess, run the script `tools/cleanup_failed_session` to reset all SOCBED machines to their original state and remove all superfluous clones and snapshots.

## Login information

For all Linux machines, the Linux username is either `root` (Internet Router, Company Router, Attacker) or `breach` (Log/Internal/DMZ Server) and the password is `breach`.
SSH access is allowed via all network interfaces.
Attention: The SSH Server on the Company Router and the Internet Router is running on the non-standard port 222!

The Samba domain controller running on the Internal Server has 101 user accounts:
The domain administrator with username `administrator` and password `breach` and 100 user accounts named `client1` through `client100`, all with password `breach`.
The domain name is `BREACH`.

There is also a local administrator account on the Client with username `breach`.
During automated simulations, this account is not used, but it's handy for installation, testing, and demonstration purposes.
By default, the Client logs in automatically as user `setup` in order to change its IP address and computer name, and then join the domain (that's why every client restarts twice).
To avoid this, you can press and hold the Shift key when Windows starts up.

There is also an SSH server running on the Client (only accessible via the management network).
Login via SSH is only possible with username `breach` and password `breach`.

The following table shows all available web interfaces and their logins:

| Machine | Service | Username | Password | URL |
| --- | --- | --- | --- | --- |
| Company Router | IPFire | admin | breach | https://192.168.56.10:444/ |
| DMZ Server | phpMyAdmin | root | breach | http://192.168.56.20/phpmyadmin/ |
| Log Server | Kibana | - | - | http://192.168.56.12:5601/app/kibana |
| Internet Router | IPFire | admin | breach | https://192.168.56.30:444/ |

## Documentation

Further documentation, including a network plan of the virtual machines, can be found in the [docs](docs/) directory.

## Contributors

SOCBED was created by [Fraunhofer FKIE](https://www.fkie.fraunhofer.de/)'s department of Cyber Analysis & Defense (CA&D) as part of the [BMBF](https://www.bmbf.de/)-funded project [PA-SIEM](https://www.forschung-it-sicherheit-kommunikationssysteme.de/projekte/pa-siem).
For more information, please contact Rafael Uetz (firstname.lastname@fkie.fraunhofer.de).

## License

The files in this repository are licensed under the GNU General Public License Version 3. See [LICENSE](LICENSE) for details.
