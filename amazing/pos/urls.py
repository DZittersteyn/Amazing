from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('pos.views',

    # generic forms

    url(r'^$', 'index'),
    url(r'^index.html$',         'index'),
    url(r'login.html$',          'login'),
    url(r'^logout.html$',        'logout'),
    url(r'^filtereduserlist$',   'filtereduserlist'),
    url(r'^userlist.html$',      'userlist'),
    url(r'^newUser.html$',       'newUser'),
    url(r'^buyLine.html$',       'buyLine'),
    url(r'^noCredit.html$',      'noCredit'),
    url(r'^spinner$',            'spinner'),
    url(r'^exchange$',           'exchange_rate'),
    url(r'^activity$',           'activity'),
    url(r'^activity/purchase_free$',           'activity_purchase_free'),
    url(r'^activity/restrictions$',            'activity_restrictions'),

    # functions that require user authentication

    url(r'^user/$',              'user'),
    url(r'^user/barcode$',       'get_user_by_barcode'),
    url(r'^user/purchases$',     'purchaselist'),
    url(r'^user/purchase$',      'purchase'),
    url(r'^user/purchaseli$',    'purchase'),
    url(r'^user/undodialog$',    'undo_dialog'),
    url(r'^user/new$',           'new_user'),
    url(r'^user/edit$',          'edit_user'),
    url(r'^consistent$',         'field_consistent'),

    url(r'^purchase$',           'transaction'),
    url(r'^passcode$',           'passcode'),

    # functions that require admin login

    # ugh, this is getting a bit nasty, so:
    # TODO: Clean up URL.py structure, at least separate admin/ etc.
    # and for next time: USE NAMED URLS! How do you keep forgetting DRY. 

    url(r'^admin.html$',            'admin'),

    url(r'^adminuserlist$',         'admin_user_list'),
    url(r'^adminoptions$',          'admin_user_options'),
    url(r'^admin_userdata$',        'admin_user_data'),
    url(r'^admin_edit_user$',       'admin_edit_user'),

    url(r'^adminactivitylist$',     'admin_activity_list'),
    url(r'^adminactivitylist/new$', 'admin_activity_list_new'),
    url(r'^activityoptions$',       'admin_activity_options'),
    url(r'^activity/edit$',         'admin_activity_edit'),
    url(r'^activity/delete$',       'admin_activity_delete'),

    url(r'^system_user/list$',      'admin_system_user_list'),
    url(r'^system_user/user$',      'admin_system_user_options'),
    url(r'^system_user/new$',       'admin_system_user_new'),
    url(r'^system_user/delete$',    'admin_system_user_delete'),
    url(r'^system_user/edit$',      'admin_system_user_edit'),

    url(r'^inventory/list$',        'admin_inventory_list'),
    url(r'^inventory/total$',       'admin_inventory_total'),
    url(r'^inventory/balance$',     'admin_inventory_balance'),
    url(r'^inventory/purchase$',    'admin_inventory_purchase'),
    url(r'^inventory/product$',     'admin_inventory_product'),
    url(r'^inventory/types$',       'admin_inventory_types'),
    url(r'^inventory/delete$',      'admin_inventory_delete'),
    url(r'^inventory/edit$',        'admin_inventory_edit'),

    url(r'^totals/list$',           'admin_totals_list'),
    url(r'^totals/result$',         'admin_totals_result'),

    url(r'^adminexportcontent$',    'admin_exportcontent'),
    url(r'^adminmanageexport$',     'admin_manage_export'),
    url(r'^export/(?P<pk>[0-9]*)$', 'get_export'),

    url(r'^user/activate$',         'admin_user_activate'),
    url(r'^user/deactivate$',       'admin_user_deactivate'),
    url(r'^user/reset$',            'admin_user_reset'),

    url(r'^credit/commit_batch$',   'admin_credit_commit_batch'),
    url(r'^credit/load_status$',    'admin_credit_load_status'),
    url(r'^credit/invalidate$',     'admin_credit_invalidate'),
    url(r'^credit/batch/list$',     'admin_credit_batch_list'),
    url(r'^credit/batch/$',         'admin_credit_batch'),
)
