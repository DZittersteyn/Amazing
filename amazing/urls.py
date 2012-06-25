from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
 #   url(r'^polls/', include('polls.urls')),
    url(r'^pos/', include('pos.urls')),
 #   url(r'^admin/', include(admin.site.urls)),

    url(r'^accounts/login/$',  login),
    url(r'^accounts/logout/$', logout),
)
