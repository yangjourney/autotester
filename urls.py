from django.conf.urls import url, include
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from patterns import patterns

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'autotester.views.home', name='home'),
    url(r'^autotester',include('autotester.script.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', admin.site.urls),
)
