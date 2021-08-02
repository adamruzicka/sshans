#!/usr/bin/env python3

# Usage: sshans.py [path_to_ansible_inventory]

from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader

import subprocess
import os
import sys

# TODO: Use argparse or something
inventory = "inventory"
if len(sys.argv) == 2:
    inventory = sys.argv[1]

loader = DataLoader()
inventory = InventoryManager(loader=loader, sources=inventory)

if inventory.hosts == {}:
    sys.exit(1)

# TODO?: Support alternatives to fzf
fzf = subprocess.Popen(["fzf"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
hostnames = inventory.hosts.keys()
hostname = fzf.communicate(bytes("\n".join(hostnames), "UTF-8"))[0].decode().strip()

if hostname == "":
    sys.exit(1)

def var(key, sources, default=None):
    result = None
    for source in sources:
        result = source.get(key, None)
        if result:
            break
    return result or default

host = inventory.hosts[hostname]
sources = [host.vars] + [group.vars for group in host.groups]
host = var("ansible_host", sources, hostname)

def ssh_option(command, option, value):
    if value:
        command.append("-o")
        command.append(f"{option}={value}")

command = ["ssh"]
if host != hostname:
    ssh_option(command, "Hostname", host)
ssh_option(command, "User", var("ansible_user", sources))
ssh_option(command, "IdentityFile", var("ansible_ssh_private_key_file", sources))
ssh_option(command, "Port", var("ansible_port", sources))
command.append(hostname)

password = var("ansible_password", sources)
if password:
    os.environ["SSHPASS"] = password
    os.execl("/usr/bin/sshpass", "sshpass", "-e", *command)
else:
    os.execl("/usr/bin/ssh", *command)
