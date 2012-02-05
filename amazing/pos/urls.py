from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('pos.views',
     url(r'^$' , 'index'),
     url(r'^user/(?P<user_id>\d+)', 'user'),
     url(r'^userlist.html', 'userlist'),
)