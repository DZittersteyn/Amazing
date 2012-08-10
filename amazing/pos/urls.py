from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('pos.views',
     url(r'^$' , 'index'),
     url(r'^index.html$' , 'index'),
     url(r'^login.html$' , 'login'),
     url(r'^logout.html$' , 'logout'),
     url(r'^filtereduserlist-(?P<beginswith>[a-zA-Z][a-zA-Z]).html$', 'filtereduserlist'),
     url(r'^userlist.html$', 'userlist'),
     url(r'^newUser.html$', 'newUser'),
     url(r'^undodialog_(?P<user_id>\d+).html$', 'undoDialog'),
     url(r'^buyLine.html$', 'buyLine'),
     url(r'^noCredit.html$', 'noCredit'),
     url(r'^user/$', 'user_edit'),
     url(r'^user/barcode$', 'get_user_by_barcode'),
     url(r'^user/(?P<user_id>\d+)$', 'user'),
     url(r'^user/(?P<user_id>\d+)/purchases$','purchaselist'),
     url(r'^user/(?P<user_id>\d+)/activate$','admin_user_activate'),
     url(r'^user/(?P<user_id>\d+)/deactivate$','admin_user_deactivate'),
     url(r'^purchase-(?P<tr_id>\d+).html$','transaction'),
     url(r'^transaction/(?P<tr_id>\d+).html$','transaction'),     
     url(r'^transactionli-(?P<tr_id>\d+).html$','transaction'),   
     url(r'^passcode.html$','passcode'),


     url(r'^admin.html$','admin'),
     url(r'^adminuserlist.html','admin_user_list'),
     url(r'^adminoptions/(?P<user_id>\d+).html','admin_user_options'),
)