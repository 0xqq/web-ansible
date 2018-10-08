
from django.shortcuts import render, redirect
from django.http import HttpResponse
import json


def render_with_user(request, template_name, context=None, content_type=None):
    user = request.user
    if user is not None:
        if context is None:
            context = {}
        context['user_local'] = user
        return render(request, template_name, context, content_type)
    else:
        return redirect("/logon?next=/web/")


class JSONResponse(HttpResponse):
    def __init__(self, data, **kwargs):
        content = json.dumps(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content=content, **kwargs)
