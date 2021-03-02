# Ansible dynamic inventory script to get data from VMware ESXI


# Technology stack
- Python 3.6+
- pyvmomi lib
- PyYAML lib


# Requirements and dependencies
- python libs from requirements.txt  
- configuration variables to connect VMware ESXI host stored in yaml configuration file OR environment variables (examples below)  


# Configuration
Configuration variables could be stored as environment variables OR in yaml configuration file `inventory.yaml` 

## Environment variables
| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
|ANSIBLE_INVENTORY_SCRIPT_ESXI_HOST|ESXI host ip address or name|string||Yes|
|ANSIBLE_INVENTORY_SCRIPT_ESXI_PORT|ESXI host port|string||Yes|
|ANSIBLE_INVENTORY_SCRIPT_ESXI_USERNAME|ESXI host username|string||Yes|
|ANSIBLE_INVENTORY_SCRIPT_ESXI_PASSWORD|ESXI host password|string||Yes|
|ANSIBLE_INVENTORY_SCRIPT_GROUP_BY|Ansible hosts grouping key|string|`vm_os_type_id`|No|

## Configuration file
`inventory.yaml` yaml configuration file example:
```yaml
---
esxi_host: "192.168.88.4"  # ESXI host ip address or name
esxi_port: 443  # ESXI host port
esxi_username: "root"  # ESXI host username
esxi_password: "PASSWORD"  # ESXI host password
group_by: "vm_os_type_id"  # Ansible hosts grouping key
```


# Usage
1. Install python requirements from requirements.txt (`pip install -r requirements.txt`).  
2. Create inventory.yaml configuration file or export environment variables.  
3. Use dynamic inventory script `inventory.py` in common with Ansible, or standalone.  
```
python inventory.py --list  # outputs VM list data json object
ansible -i inventory.py all --list-hosts  # get hosts list
ansible -i inventory.py all -m ansible.builtin.ping"  # executes ansible ad-hoc commands against inventory hosts
ansible -i inventory.py all -m raw -a "uname -a"  # executes ansible ad-hoc commands against inventory hosts
ansible -i inventory.py all -m raw -a "uname -a" --extra-vars "ansible_user=root ansible_password=XXXXXXX"  # executes ansible ad-hoc commands against inventory hosts
ansible-playbook -i inventory.py playbook.yaml  # executes ansible playbook command against inventory hosts
```


# Contributing
Please refer to each project's style and contribution guidelines for submitting patches and additions. In general, we follow the "fork-and-pull" Git workflow.

 1. **Fork** the repo on GitHub
 2. **Clone** the project to your own machine
 3. **Commit** changes to your own branch
 4. **Push** your work back up to your fork
 5. Submit a **Pull request** so that we can review your changes

NOTE: Be sure to merge the latest from "upstream" before making a pull request!


# License
Apache 2.0
