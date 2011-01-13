from django.conf.urls.defaults import *
from esmg.wiki.models import *

urlpatterns = patterns("",
    (r'^$', 'esmg.wiki.views.wikipageview'),
    (r'^edit/$', 'esmg.wiki.views.editwiki'),
    (r'^versions/(?P<version>\d+)/$', 'esmg.wiki.views.versions'),
    (r'^(?P<slug>[\w-]+)/$', 'esmg.wiki.views.wikipageview'),
    (r'^(?P<slug>[\w-]+)/edit/$', 'esmg.wiki.views.editwiki'),
    (r'^(?P<slug>[\w-]+)/versions/(?P<version>\d+)/$',
        'esmg.wiki.views.versions'),
)
