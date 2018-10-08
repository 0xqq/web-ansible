from django.conf.urls import url, include

from . import views as view

urlpatterns = [
    url(r'^$', view.index, name='index'),
    url(r'^ansible$', view.ansible_api, name="ansible"),
    url(r'^ansible/hoc$', view.ansible_hoc, name="ansible_hoc"),
]
