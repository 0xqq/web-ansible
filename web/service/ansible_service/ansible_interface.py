# -*- coding:utf-8 -*-
import json

from .ansible_api import AnsibleAPI


class AnsiInterface(AnsibleAPI):
    __this = None

    def __init__(self, resource, *args, **kwargs):
        super(AnsiInterface, self).__init__(resource, *args, **kwargs)

    @classmethod
    def instance(cls):
        if cls.__this is None:
            cls.__this = AnsiInterface({})
        return cls.__this

    @staticmethod
    def deal_result(info):
        return info

    def copy_file(self, host_list, src=None, dest=None):
        """
        copy file
        """
        module_args = "src=%s  dest=%s" % (src, dest)
        self.run(host_list, 'copy', module_args)
        result = self.get_result()
        return self.deal_result(result)

    def exec_run(self, host_list, module, args):
        self.run(host_list, module, args)
        result = self.get_result()
        return self.deal_result(result)

    def exec_command(self, host_list, cmds):
        """
        commands
        """
        self.run(host_list, 'command', cmds)
        result = self.get_result()
        return self.deal_result(result)

    def exec_shell(self, host_list, cmds):
        """
        commands
        """
        self.run(host_list, 'shell', cmds)
        result = self.get_result()
        return self.deal_result(result)

    def exec_script(self, host_list, path):
        """
        在远程主机执行shell命令或者.sh脚本
        """
        self.run(host_list, 'shell', path)
        result = self.get_result()
        return self.deal_result(result)

    def run_play(self, filenames, vars):
        self.run_playbook(filenames, vars)
        result = self.get_result()
        return self.deal_result(result)


if __name__ == "__main__":
    resource = [{"port": "22", "username": "root", "password": "ggty@2017", "ip": '10.5.4.203'},
                {"port": "22", "username": "root", "password": "ggty@2017", "ip": '10.5.4.181'}]
    interface = AnsiInterface(resource)
    # print interface.exec_shell('all', 'cd /home && ls')
    # print "copy: ", interface.copy_file(['172.20.3.18', '172.20.3.31'], src='/Users/majing/test1.py', dest='/opt')
    # print "commands: ", interface.exec_command(['172.20.3.18', '172.20.3.31'], 'hostname')
    # print "shell: ", interface.exec_script(['172.20.3.18', '172.20.3.31'], 'chdir=/home ls')
    print(interface.run_play(['/home/xiuzhu/app/ansible_workspace/jdk.yaml'],
                             {"hosts": "10.5.4.181",
                              "jdk_name": "jdk1.8.0_111",
                              "target_dir": "/usr/local"}))
