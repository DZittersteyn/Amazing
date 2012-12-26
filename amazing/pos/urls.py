from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('pos.views',

    # generic forms

    url(r'^$', 'index'),
    url(r'^index.html$',         'index'),
    url(r'^login.html$',         'login'),
    url(r'^logout.html$',        'logout'),
    url(r'^filtereduserlist$',   'filtereduserlist'),
    url(r'^userlist.html$',      'userlist'),
    url(r'^newUser.html$',       'newUser'),
    url(r'^buyLine.html$',       'buyLine'),
    url(r'^noCredit.html$',      'noCredit'),

    # functions that require user authentication

    url(r'^user/$',              'user'),
    url(r'^user/barcode$',       'get_user_by_barcode'),
    url(r'^user/purchases$',     'purchaselist'),
    url(r'^user/purchase$',      'purchase'),
    url(r'^user/purchaseli$',    'purchase'),
    url(r'^user/undodialog$',    'undo_dialog'),
    url(r'^user/new$',           'new_user'),
    url(r'^user/edit$',          'edit_user'),
    url(r'^consistent$',    'field_consistent'),

    url(r'^purchase$',           'transaction'),
    url(r'^passcode$',           'passcode'),

    # functions that require admin login

    # ugh, this is getting a bit nasty, so:
    # TODO: Clean up URL.py structure, at least separate admin/ etc.

    url(r'^admin.html$',         'admin'),

    url(r'^adminuserlist$',      'admin_user_list'),
    url(r'^adminoptions$',       'admin_user_options'),
    url(r'^admin_userdata$',     'admin_user_data'),
    url(r'^admin_edit_user$',    'admin_edit_user'),

    url(r'^adminactivitylist$',  'admin_activity_list'),
    url(r'^adminactivitylist/new$',  'admin_activity_list_new'),
    url(r'^activityoptions$',    'admin_activity_options'),

    url(r'^adminexportcontent$', 'admin_exportcontent'),
    url(r'^adminmanageexport$',  'admin_manage_export'),
    url(r'^export/(?P<pk>[0-9]*)$', 'get_export'),

    url(r'^user/activate$',      'admin_user_activate'),
    url(r'^user/deactivate$',    'admin_user_deactivate'),
    url(r'^user/reset$',         'admin_user_reset'),

)
