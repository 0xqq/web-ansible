# encoding=utf-8
from django.contrib.auth import authenticate, login, logout
from django.http import Http404
from django.shortcuts import render, redirect

from web.service.ansible_service.ansible_interface import AnsiInterface
from .models import Machine
from .service.MachineService import MachineService
from web.util.common import render_with_user, JSONResponse
from django.contrib.auth.decorators import login_required

from django.template import TemplateDoesNotExist


# @login_required
def index(request):
    res = MachineService.count_status_all()
    try:
        return render_with_user(request, 'web/index.html', {'count': res})
    except TemplateDoesNotExist:
        raise Http404("页面不存在")


def ansible_api(request):
    ip = request.GET.get("ip")
    module = request.GET.get("module")
    args = request.GET.get("args")
    interface = AnsiInterface.instance()

    return JSONResponse(interface.exec_run(ip, module, args))


def ansible_hoc(request):
    ip = request.GET.get("ip")
    module = request.GET.get("module")
    args = request.GET.get("args")
    user = request.GET.get("user")
    password = request.GET.get("password")
    port = request.GET.get("port", "22")
    resource = [{"port": port, "username": user, "password": password, "ip": ip}]
    interface = AnsiInterface(resource)

    return JSONResponse(interface.exec_run(ip, module, args))