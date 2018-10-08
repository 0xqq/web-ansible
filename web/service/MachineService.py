# -*- coding:utf-8 -*-
from django.db.models import Count

from web.models import Machine
from web.const import MACHINE_STATUS


class MachineService:

    def __init__(self):
        return

    @staticmethod
    def count_status(s):

        return Machine.objects.filter(status=s).count()

    @staticmethod
    def count_all():
        return Machine.objects.count()

    @classmethod
    def count_status_all(cls):

        res_dic = {}
        res = Machine.objects.values_list("status").annotate(Count("id"))

        for item in res:
            status = item[0]
            num = item[1]

            type = MACHINE_STATUS.get(status, None)
            if type is not None:
                res_dic[type]=num

        return res_dic
