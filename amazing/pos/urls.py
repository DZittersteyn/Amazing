from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('pos.views',
     url(r'^$' , 'index'),
     url(r'userlist.html$', 'userlist'),
     url(r'user/$', 'user_edit'),
     url(r'user/(?P<user_id>\d+)$', 'user'),
     url(r'user/(?P<user_id>\d+)/purchases$','purchaselist')
)