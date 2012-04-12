from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('pos.views',
     url(r'^$' , 'index'),
     url(r'userlist.html$', 'userlist'),
     url(r'newUser.html$', 'newUser'),
     url(r'buyLine.html$', 'buyLine'),
     url(r'noCredit.html$', 'noCredit'),
     url(r'user/$', 'user_edit'),
     url(r'user/(?P<user_id>\d+)$', 'user'),
     url(r'user/(?P<user_id>\d+)/purchases$','purchaselist')
)