# encoding=utf-8
import os
import sys
import logging

from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.plugins.callback.default import CallbackModule
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.inventory.host import Host
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase
from ansible import constants as C

from web.service.ansible_service.OdinInventory import OdinInventory

logger = logging.basicConfig()
try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ResultsCollector(CallbackBase):
    def __init__(self, *args, **kwargs):
        super(ResultsCollector, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def v2_runner_on_unreachable(self, result):
        self.host_unreachable[result._host.get_name()] = result

    def v2_runner_on_ok(self, result, *args, **kwargs):
        self.host_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        self.host_failed[result._host.get_name()] = result


class MyInventory(InventoryManager):
    """
    this is my ansible_service inventory object.
    """

    def __init__(self, resource, loader, sources=None):
        """
        resource的数据格式是一个列表字典，比如
            {
                "group1": {
                    "hosts": [{"hostname": "10.0.0.0", "port": "22", "username": "test", "password": "pass"}, ...],
                    "vars": {"var1": value1, "var2": value2, ...}
                }
            }

        如果你只传入1个列表，这默认该列表内的所有主机属于my_group组,比如
            [{"hostname": "10.0.0.0", "port": "22", "username": "test", "password": "pass"}, ...]
        """
        super(MyInventory, self).__init__(loader=loader)
        self.resource = resource
        self.gen_inventory()

    def my_add_group(self, hosts, groupname, groupvars=None):
        """
        add hosts to a group
        """
        self.add_group(groupname)
        group_dict = self.get_groups_dict()
        my_group = group_dict[groupname]
        # if group variables exists, add them to group
        if groupvars:
            for key in groupvars:
                value = groupvars.get(key)
                my_group.set_variable(key, value)

                # add hosts to group
        for host in hosts:
            # set connection variables
            host_ip = host.get('ip')
            host_port = '22'
            username = 'root'
            if 'port' in host:
                host_port = host.get("port")
            if 'username' in host:
                username = host.get("username")
            password = host.get("password")
            my_host = Host(name=host_ip, port=host_port)
            my_host.set_variable('ansible_ssh_port', host_port)
            my_host.set_variable('ansible_ssh_user', username)
            my_host.set_variable('ansible_ssh_pass', password)

            self.add_host(host_ip, group=groupname, port=host_port)
            self._inventory.set_variable(host_ip, 'ansible_ssh_port', host_port)
            self._inventory.set_variable(host_ip, 'ansible_ssh_user', username)
            self._inventory.set_variable(host_ip, 'ansible_ssh_pass', password)

            # set other variables
            for key in host:
                if key not in ["hostname", "port", "username", "password"]:
                    value = host.get(key)
                    my_host.set_variable(key, value)
                    self._inventory.set_variable(host_ip, key, value)

    def gen_inventory(self):
        """
        add hosts to inventory.
        """
        if isinstance(self.resource, list):
            self.my_add_group(self.resource, 'default_group')
        elif isinstance(self.resource, dict):
            for groupname, hosts_and_vars in self.resource.iteritems():
                self.my_add_group(hosts_and_vars.get("hosts"), groupname, hosts_and_vars.get("vars"))

        self.reconcile_inventory()


class AnsibleAPI(object):
    """
    This is a General object for parallel execute modules.
    """

    def __init__(self, resource, *args, **kwargs):
        self.resource = resource
        self.inventory = None
        self.variable_manager = None
        self.loader = None
        self.options = None
        self.passwords = None
        self.callback = None
        self.__initialize_data()
        self.results_raw = {}

    def __initialize_data(self):

        Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'timeout', 'remote_user',
                                         'ask_pass', 'private_key_file', 'ssh_common_args', 'ssh_extra_args',
                                         'sftp_extra_args',
                                         'scp_extra_args', 'become', 'become_method', 'become_user', 'ask_value_pass',
                                         'verbosity',
                                         'check', 'listhosts', 'listtasks', 'listtags', 'syntax', 'diff', 'host_key_checking'])

        self.loader = DataLoader()
        self.options = Options(connection='smart', module_path=C.DEFAULT_MODULE_PATH, forks=100, timeout=10,
                               remote_user='root', ask_pass=False, private_key_file=None, ssh_common_args=None,
                               ssh_extra_args=None,
                               sftp_extra_args=None, scp_extra_args=None, become=None, become_method=None,
                               become_user='root', ask_value_pass=False, verbosity=None, check=False, listhosts=False,
                               listtasks=False, listtags=False, syntax=False, diff=False, host_key_checking=False)

        self.passwords = dict(conn_pass=None, becomepass=None)
        if not self.resource:
            self.inventory = OdinInventory(self.loader)
        else:
            self.inventory = MyInventory(self.resource, self.loader)

        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)

    def run(self, host_list, module_name, module_args):
        """
        run module from andible ad-hoc.
        module_name: ansible_service module_name
        module_args: ansible_service module args
        """
        # create play with tasks
        play_source = dict(
            name="Ansible Play",
            hosts=host_list,
            gather_facts='no',
            tasks=[
                dict(action=dict(module=module_name, args=module_args))
            ]
        )
        play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)

        # actually run it
        tqm = None
        self.callback = ResultsCollector()
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=self.passwords,
            )
            tqm._stdout_callback = self.callback
            tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()

    def run_playbook(self, filenames, vars):
        """
        run ansible_service palybook
        """
        try:
            self.callback = ResultsCollector()

            extra_vars = vars
            self.variable_manager.extra_vars = extra_vars
            # actually run it
            executor = PlaybookExecutor(
                playbooks=filenames, inventory=self.inventory, variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options, passwords=self.passwords,
            )
            # executor._tqm._stdout_callback = self.callback
            executor._tqm._stdout_callback = CallbackModule()
            executor.run()

        except Exception as e:
            print("error:", e.message)

    def get_result(self):
        self.results_raw = {'success': {}, 'failed': {}, 'unreachable': {}}
        for host, result in self.callback.host_ok.items():
            self.results_raw['success'][host] = result._result

        for host, result in self.callback.host_failed.items():
            self.results_raw['failed'][host] = result._result.get('msg') or result._result

        for host, result in self.callback.host_unreachable.items():
            self.results_raw['unreachable'][host] = result._result['msg']

        return self.results_raw
