from django.conf.urls.defaults import *
from esmg.publications.models import Publication
from esmg.resources.models import Resource
from esmg.institutions.models import Institution, Instdiv, Subdivision, Division
from esmg.middleware import threadlocals
from django.conf import settings
#handler500 = "django.views.server_error"

resource_add_dict = {"model": Resource, "login_required": True,
        "post_save_redirect": "../%(id)s/info/"}


info_dict = {
    'paginate_by':  8,
    'allow_empty':  True,
}

urlpatterns = patterns('',
    (r'^admin/', include('django.contrib.admin.urls')),
    (r'^publications/', include('esmg.publications.urls')),
    (r'^people/', include('esmg.people.urls')),
    (r'^projects/', include('esmg.groups.urls')),
    (r'^groups/', include('esmg.groups.urls')),
    (r'^resources/', include('esmg.resources.urls')),
    #(r'^search/$', 'esmg.views.search'),
    (r'^home/$', 'esmg.people.views.home'),
    (r'^friend_requests/$', 'esmg.people.views.friend_confirms'),
    (r'^friend_request/(?P<slug>[\w-]+)/$', 'esmg.people.views.friend_request'),
    (r'^messages/$', 'esmg.comms.views.messages'),
    (r'^messages/(?P<object_id>\d+)/$', 'esmg.comms.views.notificationdetail'),
    (r'^messages/send/$', 'esmg.comms.views.send_message'),
    (r'^institutions/add/$', 'django.views.generic.create_update.create_object',
        dict(model=Institution, post_save_redirect='../done/')),
    (r'^institutions/done/$', 'django.views.generic.simple.direct_to_template',
        dict(template='institutions/addinst_done.html')),
    (r'^accounts/login/$', 'django.contrib.auth.views.login', 
            {'template_name': 'accounts/login.html'}),
    (r'^accounts/profile/$', 'django.views.generic.simple.redirect_to',
            {'url': settings.URLBASE }),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout',
            {'template_name': 'accounts/logout.html'}),
    (r'^accounts/forgotpassword/$', 'esmg.people.views.password_forgot',
            {'template_name': 'accounts/forgot.html'}),
    #get group-specific app pages and forward them on to app urls as appropriate
    (r'^(?P<group>[\w-]+)/publications/$',
        'esmg.publications.views.grouppub'),
    (r'^(?P<group>[\w-]+)/publications/', include('esmg.publications.urls')),
    (r'^(?P<group>[\w-]+)/resources/$',
        'esmg.resources.views.list', dict(type="group_list")),
    (r'^(?P<group>[\w-]+)/resources/popup/$',
        'esmg.resources.views.list', dict(type="popup_list")),
    #(r'^(?P<group>[\w-]+)/resources/search/$',
        #'esmg.resources.views.search'),
    (r"^(?P<group>[\w-]+)/resources/edit/(?P<object_id>\d+)/$", "esmg.resources.views.create_resource",
            dict(edit=True)),
    (r"^(?P<group>[\w-]+)/resources/delete/(?P<object_id>\d+)/$", "esmg.resources.views.delete_resource"),
    (r'^(?P<group>[\w-]+)/publications/search/$',
        'esmg.publications.views.search'),
    (r'^(?P<group>[\w-]+)/publications/(?P<object_id>\d+)/$',
        'esmg.publications.views.detail'),
    (r"^(?P<group>[\w-]+)/resources/add/$", 
        'esmg.resources.views.create_resource'),
    (r'^(?P<group>[\w-]+)/people/', include('esmg.people.urls')),
    (r'^(?P<group>[\w-]+)/news/$', 'esmg.comms.views.itemlist', dict(type="newsblog")),
    (r'^(?P<group>[\w-]+)/news/(?P<object_id>\d+)/$', 'esmg.comms.views.itemdetail', dict(type="newsblog")),
    (r'^(?P<group>[\w-]+)/news/add/$', 'esmg.comms.views.postitem', dict(type="newsblog")),
    (r'^(?P<group>[\w-]+)/news/edit/(?P<object_id>\d+)/$',
        'esmg.comms.views.edititem', dict(type="newsblog")),
    (r'^(?P<group>[\w-]+)/news/delete/(?P<object_id>\d+)/$',
        'esmg.comms.views.deleteitem', dict(type="newsblog")),
    (r'^(?P<group>[\w-]+)/events/$', 'esmg.comms.views.itemlist', dict(type="events")),
    (r'^(?P<group>[\w-]+)/events/(?P<object_id>\d+)/$', 'esmg.comms.views.itemdetail',dict(type="events")),
    (r'^(?P<group>[\w-]+)/events/add/$', 'esmg.comms.views.postitem', dict(type="events")),
    (r'^(?P<group>[\w-]+)/events/edit/(?P<object_id>\d+)/$',
        'esmg.comms.views.edititem', dict(type="events")),
    (r'^(?P<group>[\w-]+)/news/delete/(?P<object_id>\d+)/$',
        'esmg.comms.views.deleteitem', dict(type="events")),
    (r'^(?P<groupName>[\w-]+)/forum/', include('sphene.sphboard.urls')),
    (r'^(?P<group>[\w-]+)/manage/$', 'esmg.groups.views.manage',),
    (r'^(?P<group>[\w-]+)/wiki/', include('esmg.wiki.urls')),
    
    
    #(r'^(?P<group>[\w\-/]+)/search/$', 'esmg.views.search',
    #    dict(groupsearch=True)),
    
    # catch all sends to CMS
    (r'^sidebars/(?P<sidebar>[\d]+)/edit/$',
        'esmg.apparatus.views.editsidebar'),
    (r'^sidebars/create/$',
        'esmg.apparatus.views.createsidebar'),
    (r'^(?P<uri>[\w\-/]+)/edit/$', 'esmg.apparatus.views.editpage',
        dict(create=False)),
    (r'^(?P<uri>[\w\-/]+)/delete/$', 'esmg.apparatus.views.deletepage'),
    (r'^(?P<uri>[\w\-/]+)/move/$', 'esmg.apparatus.views.movepage'),
    (r'^(?P<uri>[\w\-/]+)/versions/(?P<version>\d+)/$',
        'esmg.apparatus.views.versions'),
    (r'^(?P<uri>[\w\-/]+)/sidebaradd/$', 'esmg.apparatus.views.addsidebar'),
    (r'^(?P<uri>[\w\-/]+)/sidebarremove/(?P<sidebar>[\d]+)/$', 'esmg.apparatus.views.removesidebar'),
    (r'^(?P<uri>[\w\-/]+)/create/$', 'esmg.apparatus.views.editpage',
        dict(create=True)),
    (r'^edit/$', 'esmg.apparatus.views.editpage', dict(uri='/', 
        create=False)),
    (r'^create/$', 'esmg.apparatus.views.editpage', dict(uri='/',
        create=True)),
    (r'^sidebaradd/$', 'esmg.apparatus.views.addsidebar', dict(uri='/')),
    (r'^sidebarremove/(?P<sidebar>[\d]+)/$', 'esmg.apparatus.views.removesidebar', dict(uri='/')),
    (r'^delete/$', 'esmg.apparatus.views.deletepage', dict(uri='/')),
    (r'^move/$', 'esmg.apparatus.views.movepage', dict(uri='/')),
    (r'^versions/(?P<version>\d+)/$', 'esmg.apparatus.views.versions',
        dict(uri='/')),
	#added this line to catch non home or people page CMS pages (where did they go before?)
    (r'^(?P<uri>[\w\-/]+)/$', 'esmg.apparatus.views.page'),
    (r'^$', 'esmg.apparatus.views.page', dict(uri='/')),
)

