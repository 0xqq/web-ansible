from ansible.inventory.data import InventoryData
from ansible.inventory.manager import InventoryManager
from ansible.module_utils.six import string_types, iteritems
from web.models import HostModel, InvGroup
from ansible.inventory.host import Host
from ansible.inventory.group import Group
import json

from django.core.cache import cache


class OdinInventoryData(InventoryData):

    def __init__(self):
        super(OdinInventoryData, self).__init__()
        self.__cache_group = None

    def _host_model_to_Host(self, host_model):
        host = Host(host_model.ip, host_model.ssh_port)
        host.set_variable('ansible_ssh_port', host_model.ssh_port)
        host.set_variable('ansible_ssh_user', host_model.ssh_user)
        host.set_variable('ansible_ssh_pass', host_model.ssh_password)

        var_dic = json.loads(host_model.var)
        for key in var_dic:
            host.set_variable(key, var_dic.get(key))

        return host

    def get_host(self, hostname):
        ''' fetch host object using name deal with implicit localhost '''
        try:
            host_model = HostModel.objects.get(name=hostname)

            return self._hostModel2Host(host_model)
        except HostModel.DoesNotExist:
            return None

    @property
    def groups(self):
        groups = cache.get('inv_groups')
        if groups is not None:
            return groups

        groups = {}
        group_models = InvGroup.objects.all()
        for group_model in group_models:
            g = Group(str(group_model.id))
            hosts = HostModel.objects.filter(gid=group_model.id)
            for host in hosts:
                g.add_host(self._hostModel2Host(host))
            groups[str(group_model.id)] = g

        all_group = Group("all")
        ungrouped_group = Group("ungrouped")
        groups["all"] = all_group
        groups["ungrouped"] = ungrouped_group
        cache.set('inv_groups', groups, 60*10)
        return self.groups

    @groups.setter
    def groups(self, value):
        return

    @property
    def hosts(self):
        hostModels = HostModel.objects.all()
        hosts = {}
        for item in hostModels:
            h = self._hostModel2Host(item)

            hosts[item.name] = h
        return hosts

    @hosts.setter
    def hosts(self, value):
        return

    def _hostModel2Host(self, hostModel):
        h = Host(hostModel.name, hostModel.ssh_port)
        h.set_variable('ansible_ssh_user', hostModel.ssh_user)
        h.set_variable('ansible_ssh_pass', hostModel.ssh_password)
        h.address = hostModel.ip

        if hostModel.var is not None:
            var_dic = json.loads(hostModel.var)
            for key in var_dic:
                value = var_dic.get(key)
                h.set_variable(key, value)

        return h

    def get_groups_dict(self):
        """
        We merge a 'magic' var 'groups' with group name keys and hostname list values into every host variable set. Cache for speed.
        """
        _groups_dict_cache = {}
        for (group_name, group) in iteritems(self.groups):
            _groups_dict_cache[group_name] = [h.name for h in group.get_hosts()]

        return _groups_dict_cache


class OdinInventory(InventoryManager):

    def __init__(self, loader):
        super(OdinInventory, self).__init__(loader=loader)

        self._inventory = OdinInventoryData()
