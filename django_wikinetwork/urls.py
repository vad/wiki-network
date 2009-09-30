from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    (r'^$', 'django.views.generic.simple.redirect_to', {'url': '/wikinetwork/'}),
    
    (r'^wikinetwork/', include('django_wikinetwork.wikinetwork.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    
    (r'^media_static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/nfsmnt/sra0/sra/setti/Source/wiki-network/django_wikinetwork/media/'}),
)
