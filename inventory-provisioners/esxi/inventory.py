#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
    @project:
    @copyright: © 2020 by vfabi
    @author: vfabi
    @support: vfabi
    @initial date: 2020-11-06 21:41:00
    @license: this file is subject to the terms and conditions defined
        in file 'LICENSE.txt', which is part of this source code package
    @description:
        Ansible dynamic inventory script to get data from VMware ESXI host.
    @arguments:
        --list - outputs VM list data json object (required by Ansible).
        --host - outputs specific VM data json object (required by Ansible).
    @requirements:
        - python libs from requirements.txt
        - configuration variables to connect VMware ESXI host stored in yaml configuration file or environment variables
            `inventory.yaml` yaml configuration file example:
                ---
                esxi_host: "192.168.88.4"  # ESXI host ip address or name
                esxi_port: 443  # ESXI host port
                esxi_username: "root"  # ESXI host username
                esxi_password: "PASSWORD"  # ESXI host password
                group_by: "vm_os_type_id"  # Ansible hosts grouping key
            environment variables used:
                ANSIBLE_INVENTORY_SCRIPT_ESXI_HOST - ESXI host ip address or name
                ANSIBLE_INVENTORY_SCRIPT_ESXI_PORT - ESXI host port
                ANSIBLE_INVENTORY_SCRIPT_ESXI_USERNAME - ESXI host username
                ANSIBLE_INVENTORY_SCRIPT_ESXI_PASSWORD - ESXI host password
                ANSIBLE_INVENTORY_SCRIPT_GROUP_BY - Ansible hosts grouping key
    @notes:
        Usage examples:
            python inventory.py --list
            ansible -i inventory.py all --list-hosts
            ansible -i inventory.py all -m ansible.builtin.ping --extra-vars "ansible_user=root ansible_password=PASSWORD"
            ansible -i inventory.py all -m raw -a "uname -a" --extra-vars "ansible_user=root ansible_password=PASSWORD"
            ansible-playbook -i inventory.py playbook.yaml --extra-vars "ansible_user=root ansible_password=PASSWORD"
    @todo:
"""

import os
import sys
import re
import json
import argparse
import atexit
import yaml
from pyVmomi import vim
from pyVim.connect import SmartConnectNoSSL, SmartConnect, Disconnect


class AnsibleInventoryESXI:

    def __init__(self, verifyssl=True):
        self.config_file = f'{os.path.dirname(os.path.abspath(__file__))}/{os.path.basename(__file__).split(".")[0]}.yaml'
        self.verifyssl = verifyssl

    def parse_args(self):
        """Parse script arguments."""

        parser = argparse.ArgumentParser(description='Get dynamic inventory data for Ansible from VMware ESXI host.')
        parser.add_argument('--list', action='store_true', help='Returns VM list data.')
        parser.add_argument('--host', help='Returns specific VM data.')
        args = parser.parse_args()

        if not args.list and not args.host:
            parser.print_help()
            parser.exit()

        return args

    def config_file_load(self):
        """Load config file data."""

        with open(self.config_file, 'r') as f:
            try:
                content = yaml.load(f, Loader=yaml.SafeLoader)
            except yaml.YAMLError as error:
                print(error)
                sys.exit(1)

        return content

    def config_get_vars(self):
        """Get config variables from config file or environment variables."""

        config_file_data = self.config_file_load()
        config_vars = {}

        try:
            config_vars['esxi_host'] = os.getenv('ANSIBLE_INVENTORY_SCRIPT_ESXI_HOST', default=config_file_data['esxi_host'])
            config_vars['esxi_port'] = os.getenv('ANSIBLE_INVENTORY_SCRIPT_ESXI_PORT', default=config_file_data['esxi_port'])
            config_vars['esxi_username'] = os.getenv('ANSIBLE_INVENTORY_SCRIPT_ESXI_USERNAME', default=config_file_data['esxi_username'])
            config_vars['esxi_password'] = os.getenv('ANSIBLE_INVENTORY_SCRIPT_ESXI_PASSWORD', default=config_file_data['esxi_password'])
            config_vars['group_by'] = os.getenv('ANSIBLE_INVENTORY_SCRIPT_GROUP_BY', default=config_file_data['group_by'])
        except Exception as e:
            print(f'Ansible inventory script get configuration variables unsuccessfull. Variable {e} can\'t be read from configuration file or from environment variables dictionary.')
            sys.exit(1)

        return config_vars

    def output_vm_list_data(self, vm_list, group_by='vm_os_type_id', use_ip=False):
        """Outputs VM list data json object back to Ansible.

        Args:
            vm_list (list): VM list data
            group_by (str): hosts grouping key, values: 'vm_os_type_id' (ESXI .guest.guestId attr value), 'vm_annotation_group' (ESXI .summary.config.annotation attr string)
            use_ip (bool): use ip addresses instead of hostnames

        Note:
            If group_by param value is 'vm_annotation_group' please be sure ESXI VM annotation contains 'group=GROUPNAME' string.
            GROUPNAME should contains [a-z], [A-Z], [0-9] and '_' chars only, otherwise host be grouped into 'ungrouped' group.
        """

        inventory = {}
        inventory['all'] = {}
        inventory['all']['children'] = []
        inventory['_meta'] = {}
        inventory['_meta']['hostvars'] = {}

        for vm in vm_list:
            if vm.guest.guestState == 'notRunning':
                continue
            if vm.guest.toolsStatus == 'toolsNotInstalled':
                continue
            hostname = vm.guest.hostName

            if group_by == 'vm_os_type_id':
                group = vm.guest.guestId or vm.guest.guestFamily
            elif group_by == 'vm_annotation_group':
                regexp = re.match("(.*)(group=)(\w+)(,|;|:|\s|$)", vm.summary.config.annotation)
                group = regexp.groups()[2] if regexp else 'ungrouped'

            if group not in inventory['all']['children']:
                inventory['all']['children'].append(group)

            if group not in inventory:
                inventory[group] = {}
                inventory[group]['hosts'] = []

            value = vm.guest.ipAddress if use_ip else hostname
            inventory[group]['hosts'].append(value)
            inventory['_meta']['hostvars'][value] = self.output_vm_data(vm_list, value, return_dict=True)

        return json.dumps(inventory, indent=4)

    def output_vm_data(self, vm_list, host, return_dict=False):
        """Outputs specific VM data json object back to Ansible.

        Args:
            vm_list (list): VM list data
            host (string): VM host name
            return_dict(bool): return dict or json object
        """

        vm_info = {}
        for vm in vm_list:
            ipaddress = vm.guest.ipAddress
            hostname = vm.guest.hostName
            if host in [ipaddress, hostname]:
                vm_info['vm_name'] = vm.name
                vm_info['vm_state'] = vm.summary.runtime.powerState
                vm_info['vm_template'] = vm.summary.config.template
                vm_info['vm_path'] = vm.summary.config.vmPathName
                vm_info['vm_instance_uuid'] = vm.summary.config.instanceUuid
                vm_info['vm_annotation'] = vm.summary.config.annotation
                vm_info['vm_spec_memory_mb'] = vm.summary.config.memorySizeMB
                vm_info['vm_spec_cpu_count'] = vm.summary.config.numCpu
                vm_info['vm_os_type_id'] = vm.guest.guestId
                vm_info['vm_os_type_name'] = vm.guest.guestFullName
                vm_info['vm_tools_status'] = vm.guest.toolsStatus
                vm_info['vm_tools_running_status'] = vm.guest.toolsRunningStatus
                vm_info['vm_hostname'] = vm.guest.hostName
                vm_info['vm_ip_address'] = vm.summary.guest.ipAddress

        if return_dict:
            return vm_info
        return json.dumps(vm_info, indent=4)

    def esxi_get_vms(self, content):
        """Get VM list data from ESXI host."""

        obj_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
        vms_list = obj_view.view
        obj_view.Destroy()

        return vms_list

    def main(self):
        args = self.parse_args()
        config = self.config_get_vars()
        connection = SmartConnect if self.verifyssl else SmartConnectNoSSL
        esxi = connection(
            host=config['esxi_host'],
            user=config['esxi_username'],
            pwd=config['esxi_password'],
            port=config['esxi_port'],
        )
        atexit.register(Disconnect, esxi)
        content = esxi.RetrieveContent()
        vm_list = self.esxi_get_vms(content)

        if args.list:
            result = self.output_vm_list_data(vm_list, group_by=config['group_by'], use_ip=True)
        elif args.host:
            result = self.output_vm_data(vm_list, host=args.host)

        print(result)


if __name__ == "__main__":
    inventory = AnsibleInventoryESXI(verifyssl=False)
    inventory.main()
