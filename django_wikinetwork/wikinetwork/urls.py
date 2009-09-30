from django.conf.urls.defaults import *

urlpatterns = patterns('django_wikinetwork.wikinetwork.views',
    (r'^$', 'index'),
    (r'^all/(?P<cls>\w*)$', 'all'),
    (r'^group/(?P<cls>\w*)$', 'group'),
    #(r'^view/(?P<m_id>\d+)/$', 'detail'),
)
