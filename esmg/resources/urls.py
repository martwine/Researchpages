from django.conf.urls.defaults import *
from esmg.resources.models import Resource
from django.conf import settings


urlpatterns = patterns("",
    (r"^$", 'esmg.resources.views.list', dict(type='full_list')),
    (r"^(?P<object_id>\d+)/$", 'esmg.resources.views.detail'),
    (r"^(?P<object_id>\d+)/info/$", "esmg.resources.views.info"),
    (r"^popup/$", 'esmg.resources.views.list',
        dict(type='popup_list')),
    (r"^add/$", 'esmg.resources.views.create_resource'),
    (r"^edit/(?P<object_id>\d+)/$", "esmg.resources.views.create_resource",
        dict(edit=True)),
    (r"^delete/(?P<object_id>\d+)/$", "esmg.resources.views.delete_resource"),
    (r"^pictures/$", "esmg.resources.views.list", dict(type="pic")),
    (r"^documents/$", "esmg.resources.views.list", dict(type="doc")),
    (r"^others/$", "esmg.resources.views.list", dict(type="res")),
)
