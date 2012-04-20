from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^polls/', include('polls.urls')),
 #   url(r'^admin/', include(admin.site.urls)),
    url(r'^pos/', include('pos.urls')),
)
