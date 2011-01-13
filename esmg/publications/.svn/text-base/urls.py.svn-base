from django.conf.urls.defaults import *
from esmg.publications.models import Publication, Author
from django.conf import settings

pubs = Publication.objects.all()
info_dict = {
    'queryset':         pubs,
    'paginate_by':      8,
    "allow_empty":      True,
    "extra_context":    {"latest_pubs": pubs.order_by("-year", "-id")[:5],
    "logo":settings.DEFAULT_LOGO}
}

urlpatterns = patterns('',
    (r'^$', 'afternoon.views.generic.list_detail.object_list', info_dict),
    (r"^(?P<object_id>\d+)/$", 'esmg.publications.views.detail'),
    (r'^add/$', 'esmg.publications.views.edit_publication'),
    (r'^edit/(?P<object_id>\d+)/$', 'esmg.publications.views.edit_publication'),
    (r'^authors/add/$', 'esmg.publications.views.add_author'),
    (r'^search/$', 'esmg.publications.views.search', info_dict),
)
