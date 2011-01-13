from django.conf.urls.defaults import *
from esmg.groups.models import Group
from django.conf import settings

esmg_groups = Group.objects.exclude(type='workgroup')

info_dict_esmg = {
    'queryset':         esmg_groups,
    #"paginate_by":      8,
    "allow_empty":      True,
    "extra_context":    {"logo": settings.DEFAULT_LOGO,},
}

urlpatterns = patterns('',
    (r'^$', 'afternoon.views.generic.list_detail.object_list',
        info_dict_esmg),
)
