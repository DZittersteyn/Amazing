from django.shortcuts import render_to_response 
from django.template.loader import render_to_string

from django.template import RequestContext

from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect

from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.servers.basehttp import FileWrapper

from itertools import chain

import datetime
import json
import threading
import HTMLParser
import re

from pos.models import *

# ugh, longfile is looooooooong. To my successor: sorry. It didn't make sense at the time either.


def ajax_required(f):
    def wrap(request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest(content='Request was not AJAX.')
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def user_auth_required(f):
    def wrap(request, *args, **kwargs):
        if(request.user.is_staff):
            return f(request, *args, **kwargs)
        if 'user' in request.REQUEST:
            user = User.objects.get(pk=request.REQUEST['user'])
            bcauth = False
            if 'barcode' in request.REQUEST:
                barcode = HTMLParser.HTMLParser().unescape(request.REQUEST['barcode'])  # fix inconsistency in sending special characters through different browsers
                bcauth = user.barcode != "" and barcode == user.barcode
            pcauth = (not user.has_passcode) or (user.passcode == "") or ('passcode' in request.REQUEST and request.REQUEST['passcode'] == user.passcode)
            if bcauth or pcauth:
                return f(request, *args, **kwargs)

        return HttpResponse(status=401, content="authenticated user required")
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def login(request):
    if request.method == 'GET':
        return render_to_response("login.html", {'retry': 'retry' in request.GET, 'next': request.GET.get('next')}, context_instance=RequestContext(request))
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)
        if user is not None and user.is_active:
            auth.login(request, user)
            return HttpResponseRedirect(request.POST.get('next', default="."))
        else:
            return render_to_response("login.html", {'retry': True, 'next': request.GET.get('next')}, context_instance=RequestContext(request))
    else:
        return HttpResponse(status=400, content='Unknown method')


@login_required
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('login.html')


@login_required
def index(request):
    return render_to_response("userselect.html",
                              {'activity': Activity.get_active(), 'mainuser': request.user.username, 'admin': request.user.is_staff}, context_instance=RequestContext(request))


def spinner(request):
    return render_to_response("spinner.html", context_instance=RequestContext(request))


def exchange_rate(request):
    return HttpResponse(status=200, content=EXCHANGE)


def activity(request):
    act = Activity.get_active()
    return HttpResponse(status=200, content=json.dumps({'act_id': act.pk, 'act_name': act.name, 'act_free': act.free}))


@login_required
def activity_purchase_free(request):
    act = Activity.get_active()
    result = act.buy_item(request.POST['productID'])

    print activity_restrictions()

    purchases = render_to_string('userdetails.html', {'purchases': Purchase.objects.filter(activity=act).order_by('-date'), 'activity': act}, context_instance=RequestContext(request))
    restrictions = render_to_string('free_content.html', {'restrictions': activity_restrictions()})

    if result['result']:
        return HttpResponse(status=200, content=json.dumps({'result': result['desc'], 'purchases': purchases, 'restrictions': restrictions}))
    else:
        return HttpResponse(status=409, content=json.dumps({'result': result['desc'], 'purchases': purchases, 'restrictions': restrictions}))


def activity_restrictions():
    activity = Activity.get_active()
    result = []
    try:
        total = TotalLimit.objects.get(associated_activity=activity)
        result.append({'desc': 'Aantal gratis kruisjes', 'left': total.limit - sum([purchase.price for purchase in Purchase.objects.filter(activity=activity)])})
    except:
        pass
    indiv = ProductLimit.objects.filter(associated_activity=activity)
    for limit in indiv:
        result.append({'desc': 'Max gratis ' + PRODUCTS[limit.product]['desc'], 'left': limit.limit - sum([purchase.price for purchase in Purchase.objects.filter(activity=activity).filter(product=limit.product)])})
    return result



@login_required
@ajax_required
def passcode(request):
    return render_to_response("passcode.html", context_instance=RequestContext(request))


@login_required
@ajax_required
def noCredit(request):
    text = None
    if 'text' in request.GET:
        text = request.GET['text']

    return render_to_response("noCredit.html", {'text': text}, context_instance=RequestContext(request))


@login_required
@ajax_required
def buyLine(request):
    return render_to_response("buyLine.html", {'pieceprice': EXCHANGE}, context_instance=RequestContext(request))


@user_auth_required
@login_required
@ajax_required
def field_consistent(request):
    obj = None
    if 'user' in request.REQUEST:
        obj = User.objects.get(pk=request.REQUEST['user'])
    elif 'activity' in request.REQUEST:
        obj = Activity.objects.get(pk=request.REQUEST['activity'])
    elif 'system_user' in request.REQUEST:
        obj = auth.models.User.objects.get(pk=request.REQUEST['system_user'])
    else:
        return HttpResponse(status=405, content='only user, system_user and activity are supported in field_consistent')

    field = request.REQUEST['field']
    value = None

    try:
        if "_date" in request.REQUEST['field']:
            field = field[:field.find('_date')]
            value = getattr(obj, field).strftime('%d/%m/%Y')
        elif "_time" in request.REQUEST['field']:
            field = field[:field.find('_time')]
            value = getattr(obj, field).strftime('%H:%M')
        else:
            value = getattr(obj, field)
    except AttributeError:
        value = ""

    if value == request.REQUEST['value']:
        return HttpResponse(status=200, content="True")
    else:
        print(str(value) + ' neq ' + request.REQUEST['value'])
        return HttpResponse(status=200, content="False")


@user_auth_required
@login_required
@ajax_required
def purchase(request):
    if request.method == 'POST':
        purchase = Purchase.objects.get(pk=request.POST['purchaseid'])
        price = purchase.price

        if request.POST['valid'] == 'true':
            if purchase.valid == 0:
                if purchase.user.get_credit() >= price or request.user.is_staff:
                    purchase.valid = 1
                    purchase.save()

                    return render_to_response("transactionli.html", {'purchase': Purchase.objects.get(pk=request.POST['purchaseid'])}, context_instance=RequestContext(request))
                else:
                    return HttpResponse(status=409, content='not enough credits')
            else:
                return HttpResponse(status=400, content='trying to redo a valid purchase')
        elif request.POST['valid'] == 'false':
            if purchase.valid == 1:
                if purchase.user.get_credit() >= -price or request.user.is_staff:
                    purchase.valid = 0
                    purchase.save()

                    return render_to_response("transactionli.html", {'purchase': Purchase.objects.get(pk=request.POST['purchaseid'])}, context_instance=RequestContext(request))
                else:
                    return HttpResponse(status=409, content='not enough credits')
            else:
                return HttpResponse(status=400, content='trying to undo an invalid purchase')
        else:
            return HttpResponse(status=400, content='mode unsupported')
    else:
        return render_to_response("transactionli.html", {'purchase': Purchase.objects.get(pk=request.GET['purchaseid'])}, context_instance=RequestContext(request))


@user_auth_required
@login_required
@ajax_required
def purchaselist(request):
    purchases = Purchase.objects.filter(user=request.REQUEST['user']).order_by('-date')[:40]
    return render_to_response("userdetails.html", {'purchases': purchases, 'map': PRODUCTS}, context_instance=RequestContext(request))


@user_auth_required
@login_required
@ajax_required
def undo_dialog(request):
    user_id = request.GET['user']
    if(request.user.is_staff):
        purchases = Purchase.objects.filter(user=user_id).order_by('-date')
        purchases_old = None
        if 'activity' in request.REQUEST and not request.REQUEST['activity'] == 'all':
            purchases = purchases.filter(activity=request.REQUEST['activity'])
    else:
        cutoff = datetime.datetime.now() - datetime.timedelta(hours=2)
        purchases = Purchase.objects.filter(user=user_id).order_by('-date').exclude(date__lte=cutoff)
        purchases_old = Purchase.objects.filter(user=user_id).order_by('-date').exclude(date__gt=cutoff)[0:15]
    user_name = User.objects.get(pk=user_id).name
    return render_to_response("undodialog.html", {'user_name': user_name, 'user_id': user_id, 'purchases': purchases, 'purchases_old': purchases_old}, context_instance=RequestContext(request))


@login_required
@ajax_required
def newUser(request):
    return render_to_response("newUser.html", context_instance=RequestContext(request))


@login_required
@ajax_required
def filtereduserlist(request):
    beginswith = request.GET['beginswith']
    users = []
    for char in beginswith:
        users.extend(User.objects.filter(name__startswith=char).extra(select={'lower_name': 'lower(name)'}).order_by('lower_name').filter(active=True))

    recent_users = []
    old_users = []
    for user in users:
        latest = user.get_latest_purchase_date()
        print latest
        if not latest or latest < datetime.datetime.now() - datetime.timedelta(days=90):
            old_users.append(user)
        else:
            recent_users.append(user)

    return render_to_response("filtereduserlist.html", {'filter': beginswith, 'users': recent_users, 'old_users': old_users})


@login_required
@ajax_required
def userlist(request):
    filters = []

    a = ord('a')
    for l in range(0, 25, 2):
        filters.append("".join((chr(l + a), chr(l + a + 1))))

    return render_to_response("userlist.html", {'filters': filters, 'admin': request.user.is_staff, 'products': PRODUCTS}, context_instance=RequestContext(request))


@login_required
@ajax_required
def new_user(request):
    if request.method == 'POST':
        if request.POST['mode'] == 'new':
            u = User(
                name=request.POST['name'],
                address=request.POST['address'],
                city=request.POST['city'],
                bank_account=request.POST['bank_account'],
                email=request.POST['email'],
                barcode=request.POST['barcode'],
                has_passcode=True if request.POST['has_passcode'] == "True" else False,
                passcode=request.POST['passcode']
                )
            u.save()
            return HttpResponse(status=200, content=u.pk)


@user_auth_required
@login_required
@ajax_required
def edit_user(request):
    if request.method == 'POST':
        if request.POST['mode'] == 'edit':
            u = User.objects.get(pk=request.POST['user'])
            u.name = request.POST['new_name']
            u.address = request.POST['new_address']
            u.city = request.POST['new_city']
            u.bank_account = request.POST['new_bank_account']
            u.email = request.POST['new_email']
            u.barcode = request.POST['new_barcode']
            if request.POST['changed_passcode'] == "True":
                u.has_passcode = True if request.POST['has_passcode'] == "True" else False
                u.passcode = request.POST['new_passcode']
            u.save()
            return HttpResponse(status=200, content=u.pk)
        else:
            return HttpResponse(status=400, content='trying to edit from a new_user dialog')
    else:
        return HttpResponse(status=400, content='GET not supported, use user/')


@login_required
@ajax_required
def get_user_by_barcode(request):
    if 'barcode' in request.GET:
        try:
            u = User.objects.get(barcode=request.GET['barcode'])
        except User.DoesNotExist:
            return HttpResponse(status=404, content="user does not exist")
        except User.MultipleObjectsReturned:
            users = User.objects.filter(barcode=request.GET['barcode'])
            return HttpResponse(status=409, content="Multiple users have the same barcode! Offending users: " + ', '.join([us.name for us in users]))
        request.GET = request.GET.copy()
        request.GET['user'] = u.pk
        return user(request)
    else:
        return HttpResponse(status=400, content="no barcode submitted")


@user_auth_required
@login_required
@ajax_required
def user(request):

    user = User.objects.get(pk=request.REQUEST['user'])
    if user is None:
        return HttpResponse(status=404, content="user does not exist")
    if request.method == 'GET':
        data = user.as_dict()
        data['password'] = "blocked"
        data = json.dumps(data)
        return HttpResponse(data, mimetype='application/json')
    elif request.method == 'POST':

        activity = Activity.get_active()
        if 'activity' in request.POST:
            activity = Activity.objects.get(pk=request.POST['activity'])

        amount = 1
        if 'amount' in request.POST:
            amount = int(request.POST['amount'])

        if request.POST['type'] == 'credit':
            if user.buy_credit(request.POST['credittype'], amount, activity, request.user.is_staff):
                return HttpResponse(status=200)
            else:
                return HttpResponse(status=500, content='Incassomatic returned an error')
        elif request.POST['type'] == 'product':
            category = None
            if 'productID' in request.POST:
                category = request.POST['productID']
            else:
                try:
                    prod = Product.objects.get(barcode=request.POST['product_barcode'])
                    amount = prod.amount
                    category = prod.category
                except Product.DoesNotExist:
                    return HttpResponse(status=404, content='This barcode is not known. Please contact an admin.')
                except Product.MultipleObjectsReturned:
                    return HttpResponse(status=409, content='This barcode is associated with more than one product. Please contact an admin.')
            result = user.buy_item(category, amount, activity, request.user.is_staff)
            if result['result']:
                return HttpResponse(status=200, content=result['desc'])
            else:
                return HttpResponse(status=409, content=result['desc'])


def admin(request):
    if request.user.is_staff:
        return render_to_response('admin.html', context_instance=RequestContext(request))
    else:
        return HttpResponse(status=401, content="You are not admin. Log in via /pos/login.html or go <a href='javascript:history.back()'>back</a>.  ")


@ajax_required
@staff_member_required
def admin_user_options(request):
    user = User.objects.get(pk=request.REQUEST['user'])

    activities = Activity.objects.all().order_by('-date')

    activities = list(chain(
        Activity.objects.filter(end=None).filter(start=None).exclude(pk=Activity.get_normal_sale().pk),
        Activity.objects.filter(end=None).exclude(start=None).order_by('-start').exclude(pk=Activity.get_normal_sale().pk),
        [Activity.get_normal_sale()],
        Activity.objects.exclude(end=None).order_by('-end')))

    resp = admin_user_data_dict(request)

    debits = Signed_debit.objects.filter(user=user)
    purcs = Purchase.objects.filter(user=user).filter(product__in=CREDITS)

    # valid signed debits with corresponding valid purchases (correct)
    correct_qset = debits.filter(valid=True).filter(purchase__valid=True)

    signed_purcs = [debit.purchase for debit in debits]
    # valid purchases without corresponding signed debit (paying too little)
    unsigned_purcs = [p for p in purcs if p not in signed_purcs and p.valid]
    unsigned_purcs_correct = [p for p in purcs if p not in signed_purcs and not p.valid]

    invalid_debit = debits.filter(valid=False).filter(purchase__valid=True)

    # invalid purchases without corresponding signed debit (correct)
    unsigned_correct = debits.filter(valid=False).filter(purchase__valid=False)

    # valid signed debits without corresponding purchase (paying too much)
    wrongly_signed = debits.filter(valid=True).filter(purchase__valid=False)

    debit_dict = []
    for debit in correct_qset:
        debit_dict.append({'key': debit.purchase.credit_key, 'batchnumber': debit.batchnumber, 'purcdate': debit.purchase.date, 'signdate': debit.date, 'value': debit.purchase.price, 'status': 'Valid purchase and signed debit', 'icon': 'check_t'})
    for debit in invalid_debit:
        debit_dict.append({'key': debit.purchase.credit_key, 'batchnumber': debit.batchnumber, 'purcdate': debit.purchase.date, 'signdate': debit.date, 'value': debit.purchase.price, 'status': 'Debit is invalid!', 'icon': 'cross_t'})
    for purchase in unsigned_purcs:
        debit_dict.append({'key': purchase.credit_key, 'batchnumber': 'N/A', 'purcdate': purchase.date, 'signdate': 'N/A', 'value': purchase.price, 'status': 'No signed debit available! Might not yet have been imported.', 'icon': 'cross_t'})
    for purchase in unsigned_purcs_correct:
        debit_dict.append({'key': purchase.credit_key, 'batchnumber': 'N/A', 'purcdate': purchase.date, 'signdate': 'N/A', 'value': purchase.price, 'status': 'No signed debit available, but the debit has been undone.', 'icon': 'info_t'})
    for debit in unsigned_correct:
        debit_dict.append({'key': debit.purchase.credit_key, 'batchnumber': debit.batchnumber, 'purcdate': debit.purchase.date, 'signdate': debit.date, 'value': debit.purchase.price, 'status': 'Both purchase and debit are invalid, no problem.', 'icon': 'info_t'})
    for debit in wrongly_signed:
        debit_dict.append({'key': debit.purchase.credit_key, 'batchnumber': debit.batchnumber, 'purcdate': debit.purchase.date, 'signdate': debit.date, 'value': debit.purchase.price, 'status': 'Debit was signed, but purchase is invalid. User is paying too much!', 'icon': 'exclaim_t'})

    debit_dict = sorted(debit_dict, key=lambda instance: instance['purcdate'])

    resp['user'] = user.as_dict()
    resp['activities'] = activities
    resp['debits'] = debit_dict

    return render_to_response('admin/user/user_options.html', resp, context_instance=RequestContext(request))


@ajax_required
@staff_member_required
def admin_user_deactivate(request):
    user = User.objects.get(pk=request.REQUEST['user'])
    user.active = False
    user.save()
    return HttpResponse(status=200, content="User deactivated")


@ajax_required
@staff_member_required
def admin_user_activate(request):
    user = User.objects.get(pk=request.REQUEST['user'])
    user.active = True
    user.save()
    return HttpResponse(status=200, content="User deactivated")


@ajax_required
@staff_member_required
def admin_user_list(request):
    users = User.objects.all().extra(select={'lower_name': 'lower(name)'}).order_by('lower_name')
    return render_to_response('admin/user/user_list.html', {'users': users}, context_instance=RequestContext(request))


@ajax_required
@staff_member_required
def admin_user_reset(request):
    user = User.objects.get(pk=request.REQUEST['user'])
    user.has_passcode = False
    user.passcode = ''
    user.save()
    return HttpResponse(status=200, content="User passcode reset")


@ajax_required
@staff_member_required
def admin_user_data(request):
    return render_to_response('admin/user/userdata.html', admin_user_data_dict(request), context_instance=RequestContext(request))


def admin_user_data_dict(request):
    purchases = Purchase.objects.filter(user=request.REQUEST['user'])
    if 'activity' in request.REQUEST and not request.REQUEST['activity'] == 'all':
        purchases = purchases.filter(activity=request.REQUEST['activity'])

    purchases = purchases.filter(valid=True)
    res = {}
    p = admin_purchase_qset_to_dict(purchases)
    res['products'] = p
    res['user'] = request.REQUEST['user']
    return res


def admin_purchase_qset_to_dict(purchase_qset):
    p = {}

    for prod in PRODUCTS.keys():
        p[prod] = {'number': 0, 'desc': PRODUCTS[prod]['desc']}

    for purchase in purchase_qset:
        if purchase.product in PRODUCTS:
            p[purchase.product]['number'] += purchase.price

    return p


@staff_member_required
@ajax_required
def admin_activity_list(request):
    now = datetime.datetime.now()
    invalid = Activity.objects.filter(start=None).exclude(pk=Activity.get_normal_sale().pk)
    pending = Activity.objects.filter(start__gt=now)
    active = list(chain(Activity.objects.filter(start__lt=now).exclude(end__lt=now).order_by('-start').exclude(pk=Activity.get_normal_sale().pk), [Activity.get_normal_sale()]))
    done = Activity.objects.filter(end__lt=now).order_by('-end')
    return render_to_response('admin/activity/activity_list.html', {'invalid': invalid, 'pending': pending, 'active': active, 'done': done}, context_instance=RequestContext(request))


@staff_member_required
@ajax_required
def admin_activity_edit(request):
    regsale = Activity.get_normal_sale()
    act = Activity.objects.get(pk=request.POST['id'])

    if act.pk == regsale.pk:
        return HttpResponse(status=409, content='Changing regular sale is not permitted')

    act.name = request.POST['name']
    act.responsible = request.POST['responsible']
    act.note = request.POST['note']
    act.free = request.POST['free'] == 'true'

    TotalLimit.objects.filter(associated_activity=act).delete()
    ProductLimit.objects.filter(associated_activity=act).delete()
    for key in [key for key in request.POST.keys() if re.match('_restriction_', key)]:
        cat = key.replace('_restriction_', '')
        if cat == 'TOTAL_RESTRICTION':
            TotalLimit(associated_activity=act, limit=request.POST[key]).save()
        else:
            ProductLimit(associated_activity=act, product=cat, limit=request.POST[key]).save()

    if request.POST['start'] != ' ':
        act.start = datetime.datetime.strptime(request.POST['start'], '%d/%m/%Y %H:%M')
    else:
        act.start = None

    if request.POST['end'] != ' ':
        act.end = datetime.datetime.strptime(request.POST['end'], '%d/%m/%Y %H:%M')
    else:
        act.end = None

    act.save()
    return HttpResponse(status=200)


@staff_member_required
@ajax_required
def admin_activity_delete(request):
    activity = Activity.objects.get(pk=request.POST['id'])
    if Purchase.objects.filter(activity=activity).filter(valid=True).exists():
        return HttpResponse(status=409, content="Can't delete activity with purchases.")
    activity.delete()
    return HttpResponse(status=200)


@staff_member_required
@ajax_required
def admin_activity_list_new(request):
    if request.POST['name'] == "":
        return HttpResponse(status=409, content="Name must not be empty")
        #TODO: [a-z0-9][a-z0-9 ]*[a-z0-9] match.

    Activity(name=request.POST['name']).save()
    return HttpResponse(status=200)


@ajax_required
@staff_member_required
def admin_activity_options(request):
    activity = Activity.objects.get(pk=request.GET['activity'])
    purchases = Purchase.objects.filter(activity=activity).filter(valid=True)
    p = admin_purchase_qset_to_dict(purchases)
    resp_autocomplete = [resp['responsible'] for resp in Activity.objects.all().values('responsible').distinct()]
    totallimit = None
    try:
        totallimit = TotalLimit.objects.get(associated_activity=activity)
    except:
        pass
    productlimit = ProductLimit.objects.filter(associated_activity=activity)

    return render_to_response('admin/activity/activity_content.html', {'activity': activity, 'products': p, 'resp_auto': resp_autocomplete, 'totallimit': totallimit, 'productlimit': productlimit}, context_instance=RequestContext(request))


@staff_member_required
@ajax_required
def admin_system_user_list(request):
    systemusers = auth.models.User.objects.all()
    return render_to_response('admin/system_user/system_user_list.html', {'systemusers': systemusers}, context_instance=RequestContext(request))


@staff_member_required
@ajax_required
def admin_system_user_options(request):
    user = auth.models.User.objects.get(pk=request.GET['user'])
    return render_to_response('admin/system_user/system_user_options.html', {'systemuser': user, 'is_admin': user.is_staff, 'is_su': user.is_superuser}, context_instance=RequestContext(request))


@staff_member_required
@ajax_required
def admin_system_user_new(request):
    if request.POST['name'] != '' and request.POST['password'] != '':
        user = auth.models.User.objects.create_user(username=request.POST['name'], password=request.POST['password'])
        user.save()
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=409, content='Username or password was empty')


@staff_member_required
@ajax_required
def admin_system_user_edit(request):
    user = auth.models.User.objects.get(pk=request.POST['system_user'])
    user.username = request.POST['name']
    user.email = request.POST['email']
    if request.POST['password'] != "":
        user.set_password(request.POST['password'])
    user.is_staff = request.POST['admin'] == 'true'
    user.is_superuser = request.POST['su'] == 'true'
    user.save()
    return HttpResponse(status=200)


@staff_member_required
@ajax_required
def admin_system_user_delete(request):
    user = auth.models.User.objects.get(pk=request.POST['system_user'])
    if user == request.user:
        return HttpResponse(status=409, content='You can not delete yourself')
    else:
        user.delete()
        return HttpResponse(status=200)


@staff_member_required
@ajax_required
def admin_totals_list(request):
    if 'pk' in request.REQUEST:
        items = Inventory_balance_product.objects.filter(inventory=Inventory_balance.objects.get(pk=request.GET['pk']))
        response_data = {}
        for item in items:
            description = dict(PRODUCTS.items() + CREDITS.items())[item.category]['desc']
            response_data[item.category] = {'modification': item.modification, 'description': description}
        return HttpResponse(json.dumps(response_data), content_type="application/json")
    else:
        balances = Inventory_balance.objects.all()
        return render_to_response('admin/totals/totals_select.html', {'balances': balances})


def add_or_create(purcs, date, category, value):
    if date not in purcs:
        purcs[date] = {}
    if category in purcs[date]:
        purcs[date][category] += value
    else:
        purcs[date][category] = value


def compute_absolutes(start, end=None):
    """computes the absolute inventory numbers between inventory_balances start and end, excluding end."""
    inventory_purchases = Inventory_purchase.objects.filter(date__gte=start.date)
    user_purchases = Purchase.objects.filter(date__gte=start.date)
    if end is not None:
        inventory_purchases = inventory_purchases.filter(date__lte=end.date)
        user_purchases = user_purchases.filter(date__lte=end.date)

    #  merge user purchases and inventory purchases

    purchases = {}
    for up in user_purchases:
        add_or_create(purchases, up.date, up.product, -up.price)
    for ip in inventory_purchases:
        products = Inventory_purchase_product.objects.filter(inventory=ip)
        for product in products:
            add_or_create(purchases, ip.date, product.category, product.modification)

    #  set up values for absolutes
    start_prods = Inventory_balance_product.objects.filter(inventory=start)

    purc_cats = []
    for key in purchases.keys():
        for item in purchases[key]:
                purc_cats.append(item)

    categories = set([prod.category for prod in start_prods] +
                     purc_cats)  # TODO: there has to be a better way to do this.

    absolutes = {}
    absolutes[start.date] = {}
    for category in categories:
        if category in [prod.category for prod in start_prods]:
            absolutes[start.date][category] = start_prods.get(category=category).modification
        else:
            absolutes[start.date][category] = 0

    #  calculate absolutes
    dates = sorted(purchases.keys())
    curdate = start.date
    for date in dates:
        absolutes[date] = {}
        for category in absolutes[curdate]:
            absolutes[date][category] = absolutes[curdate][category]
        for category in purchases[date]:
            absolutes[date][category] += purchases[date][category]
        curdate = date

    return (absolutes, absolutes[curdate])



@staff_member_required
@ajax_required
def admin_totals_result(request):
    # Fixed, killed off the bunny. Will clean up the bunny in the next commit.

    # (~\       _
    #  \ \     / \
    #   \ \___/ /\\
    #    | X X |  ~
    #    ( =v= )
    #     ` ^ '

    start = Inventory_balance.objects.get(pk=request.GET['from'])
    end = Inventory_balance.objects.get(pk=request.GET['to'])
    relevant_balances = Inventory_balance.objects.filter(date__range=(start.date, end.date)).order_by('date')

    absolutes = {}
    loss = {}
    loss[relevant_balances[0].date] = {}

    for i in range(0, len(relevant_balances)-1):
        current = relevant_balances[i]
        next = None
        next_prods = {}
        if i != len(relevant_balances) - 1:
            next = relevant_balances[i + 1]
            next_prods = Inventory_balance_product.objects.filter(inventory=next)

        (new_abs, last) = compute_absolutes(start=current, end=next)

        if next is not None:
            bala = set([next_prod.category for next_prod in next_prods])
            prev = set(last.keys())

            loss[next.date] = {}

            for category in bala | prev:
                bala_val = next_prods.get(category=category).modification if category in bala else 0
                prev_val = last[category] if category in prev else 0
                currloss = loss[current.date][category] if category in loss[current.date] else 0

                loss[next.date][category] = currloss + bala_val - prev_val

            absolutes[next.date] = {}
            for category in bala:
                absolutes[next.date][category] = next_prods.get(category=category).modification

        absolutes.update(new_abs)

    print '-----------------------'
    for key in sorted(absolutes.keys()):
        print absolutes[key]
    print '-----------------------'
    for key in sorted(loss.keys()):
        print loss[key]
    print '-----------------------'

    # split purchases and losses in two different graphs, and create the .csv we need for the graph.
    # TODO: Implement this as actual request with JSON response, as the library supports it.
    product_graph = ['"Date,Inventory,Loss\\n"']

    graph_dates = absolutes.keys() + loss.keys()
    graph_dates = sorted(set(graph_dates))

    for date in graph_dates:

        product_val = {'val': 0, 'edited': False}
        product_loss = {'val': 0, 'edited': False}
        if date in absolutes:
            for category in set(absolutes[date].keys()) & set(PRODUCTS.keys()):
                product_val['val'] += absolutes[date][category]
            product_val['edited'] = True
        if date in loss:
            for category in set(loss[date].keys()) & set(PRODUCTS.keys()):
                product_loss['val'] -= loss[date][category]
            product_loss['edited'] = True

        product_val = str(product_val['val']) if product_val['edited'] else ''
        product_loss = str(product_loss['val']) if product_loss['edited'] else ''
        product_graph += ['"' + (', '.join([date.strftime("%Y-%m-%d %H:%M:%S"), product_val, product_loss])) + '\\n"']

    return render_to_response('admin/totals/totals_detail.html', {
        'startdate': int(unix_time_millis(start.date - datetime.timedelta(days=1))),
        'enddate': int(unix_time_millis(end.date + datetime.timedelta(days=1))),
        'purchase_graph': '+ \n'.join(product_graph),
        'loss': loss[end.date],
    }, context_instance=RequestContext(request))




@staff_member_required
@ajax_required
def admin_inventory_total(request):
    prods = inventory_totals()
    return render_to_response('admin/inventory/inventory_total.html', {'products': prods}, context_instance=RequestContext(request))


def inventory_totals():
    Inventory_balance.init()
    last_balance = Inventory_balance.objects.latest(field_name='date')

    last_balance_items = Inventory_balance_product.objects.filter(inventory=last_balance)
    relevant_purchases = Inventory_purchase.objects.filter(date__gte=last_balance.date)
    relevant_user_purchases = Purchase.objects.filter(date__gte=last_balance.date)

    prods = {}

    for item in PRODUCTS:
        prods[item] = {'desc': PRODUCTS[item]['desc'], 'val': 0}

    for entry in last_balance_items:
        print entry
        if entry.category in PRODUCTS:
            prods[entry.category] = {'desc': PRODUCTS[entry.category]['desc'], 'val': entry.modification}

    for entry in relevant_purchases:
        relevant_purchase_entries = Inventory_purchase_product.objects.filter(inventory=entry)
        for purchase in relevant_purchase_entries:
            if purchase.category in prods:
                prods[purchase.category]['val'] += purchase.modification

    for user_purchase in relevant_user_purchases:
        if user_purchase.valid:
            if user_purchase.product in prods:
                prods[user_purchase.product]['val'] -= user_purchase.price

    return prods


@staff_member_required
@ajax_required
def admin_inventory_list(request):
    balance = Inventory_balance.objects.all()
    purchase = Inventory_purchase.objects.all()

    inventories = sorted(
        list(chain(balance, purchase)),
        key=lambda instance: instance.date)

    invdict = {}
    entrynum = 0
    for inventory in inventories:
        entry = {}
        entry['pk'] = inventory.pk
        invtype = 'purchase' if isinstance(inventory, Inventory_purchase) else 'balance'
        entry['type'] = invtype
        entry['date'] = inventory.date
        entry['desc'] = invtype.title()
        entry['description'] = inventory.description
        print inventory.description
        entry['sign'] = '+' if invtype == 'purchase' else '='
        entry['total'] = 0
        entry['changes'] = {}

        this_change = {}
        if isinstance(inventory, Inventory_purchase):
            this_change = Inventory_purchase_product.objects.filter(inventory=inventory)
        elif isinstance(inventory, Inventory_balance):
            this_change = Inventory_balance_product.objects.filter(inventory=inventory)

        for inv_change in this_change:
            if not inv_change.category in entry['changes']:
                entry['changes'][inv_change.category] = {}
                if inv_change.category in PRODUCTS:
                    entry['changes'][inv_change.category]['desc'] = PRODUCTS[inv_change.category]['desc']
                elif inv_change.category in CREDITS:
                    entry['changes'][inv_change.category]['desc'] = CREDITS[inv_change.category]['desc']
                else:
                    entry['changes'][inv_change.category]['desc'] = inv_change.category
                entry['changes'][inv_change.category]['num'] = 0
            entry['changes'][inv_change.category]['num'] += inv_change.modification
            entry['total'] += inv_change.modification
        entrynum += 1
        if invtype == 'purchase':
            if entry['total'] < 0:
                entry['desc'] = 'Loss'
            entry['total'] = '%+d' % entry['total']
            for change in entry['changes']:
                entry['changes'][change]['num'] = '%+d' % entry['changes'][change]['num']
        else:
            entry['total'] = ''
        invdict[entrynum] = entry

    return render_to_response('admin/inventory/inventory_list.html', {'inventory': invdict}, context_instance=RequestContext(request))


@staff_member_required
@ajax_required
def admin_inventory_product(request):
    if request.method == 'GET':
        try:
            prod = Product.objects.get(barcode=request.GET['barcode'])
        except Product.DoesNotExist:
            return HttpResponse(status=404, content='Product matching barcode does not exist.')
        except Product.MultipleObjectsReturned:
            return HttpResponse(status=509, content='More than one product has the same barcode, please delete this barcode.')
        proddict = {}
        proddict['desc'] = prod.description
        proddict['num'] = prod.amount
        proddict['category'] = prod.category
        proddict['categorydesc'] = PRODUCTS[prod.category]['desc']
        return HttpResponse(status=200, content=json.dumps(proddict), mimetype='application/json')
    else:
        mode = request.POST['mode']
        if mode == 'delete':
            product = Product.objects.filter(barcode=request.POST['barcode'])
            desc = " ".join([p.description for p in product])
            product.delete()
            return HttpResponse(status=200, content='Deleted product: ' + desc)
        elif mode == 'add':
            if not Product.objects.filter(barcode=request.POST['barcode']).exists():
                Product(barcode=request.POST['barcode'],
                        category=request.POST['category'],
                        amount=int(request.POST['amount']),
                        description=request.POST['description']).save()
                return HttpResponse(status=200, content='Created product successfully')
            else:
                return HttpResponse(status=509, content='product with this barcode already exists')
        else:
            return HttpResponseBadRequest(content='Only "delete" and "add" are permitted modes')


@staff_member_required
@ajax_required
def admin_inventory_delete(request):
    if request.POST['type'] == 'balance':
        Inventory_balance.objects.get(pk=request.POST['pk']).delete()
    elif request.POST['type'] == 'purchase':
        Inventory_purchase.objects.get(pk=request.POST['pk']).delete()
    return HttpResponse(status=200, content='Inventory successfully deleted')


@staff_member_required
@ajax_required
def admin_inventory_edit(request):
    if request.POST['type'] == 'balance':
        new = Inventory_balance.objects.get(pk=request.POST['pk'])
        new.description = request.POST['new_desc']
        new.save()
    elif request.POST['type'] == 'purchase':
        new = Inventory_purchase.objects.get(pk=request.POST['pk'])
        new.description = request.POST['new_desc']
        new.save()
    return HttpResponse(status=200, content='Inventory successfully deleted')


@staff_member_required
@ajax_required
def admin_inventory_balance(request):
    description = request.POST.get('description', '')
    inv = None
    if 'activity' in request.POST:
        inv = Inventory_balance(description=description, activity=Activity.objects.get(pk=request.POST['activity']))
    else:
        inv = Inventory_balance(description=description)
    inv.save()

    prods = inventory_totals()

    for product in prods:
        if product in request.POST:
            mod = int(request.POST[product]) - prods[product]['val']
            if mod != 0:
                Inventory_balance_product(inventory=inv, category=product, modification=mod).save()

    return HttpResponse(status=200, content='New balance created')


@staff_member_required
@ajax_required
def admin_inventory_purchase(request):
    if not Inventory_balance.objects.all().exists():
        Inventory_balance.init()

    description = request.POST.get('description', '')
    inv = Inventory_purchase(description=description)
    inv.save()
    for product in PRODUCTS:
        if product in request.POST:
            Inventory_purchase_product(inventory=inv, category=product, modification=int(request.POST[product])).save()
    inv.save()
    return HttpResponse(status=200, content='Purchase successful.')


@staff_member_required
@ajax_required
def admin_inventory_types(request):
    return render_to_response('admin/inventory/inventory_types.html', {'products': PRODUCTS}, context_instance=RequestContext(request))


@staff_member_required
@ajax_required
def admin_undo_dialog(request):
    user_id = request.GET['user']
    purchases = Purchase.objects.filter(user=user_id).order_by('-date')
    user_name = User.objects.get(pk=user_id).name
    return render_to_response("undodialog.html", {'user_name': user_name, 'user_id': user_id, 'purchases': purchases, 'purchases_old': None, 'admin': True}, context_instance=RequestContext(request))


@staff_member_required
@ajax_required
def admin_exportcontent(request):
    balances = Inventory_balance.objects.all().order_by('date')
    for i in range(0, len(balances)-1):
        start = balances[i].date
        end = balances[i+1].date
        Export.objects.get_or_create(start=start, end=end, filename=start.strftime("%Y-%m-%d") + "_to_" + end.strftime("%Y-%m-%d") + ".csv")
    return render_to_response('admin/export/export_content.html', {'exports': Export.objects.all()}, context_instance=RequestContext(request))


@staff_member_required
@ajax_required
def admin_manage_export(request):
    export = Export.objects.get(pk=request.REQUEST['export'])
    if 'start' in request.REQUEST:
        export.running = True
        t = threading.Thread(target=generate_export, args=[export])
        t.setDaemon(True)
        t.start()
        return HttpResponse(status=200, content='export started')
    else:
        if export.end > datetime.datetime.now():
            return HttpResponse(status=200, content="Can't export current month")
        if not export.done:
            if not export.running:
                return HttpResponse(status=200, content='<button class="exportbutton" id="export-' + str(export.pk) + '">Export</button>')
            else:
                return HttpResponse(status=200, content='In progress: ' + str(export.progress) + '%')
        else:
            return HttpResponse(status=200, content='<button class="downloadbutton" id="export-' + str(export.pk) + '">Download</button>')


@staff_member_required
def get_export(request, pk):
    export = Export.objects.get(pk=pk)
    response = HttpResponse(FileWrapper(open(export.filename, 'r')), content_type='text/csv', mimetype='application/x-download')
    response['Content-Disposition'] = 'attachment; filename=' + export.filename
    return response


def generate_export(export):
    num_todo = Purchase.objects.all().count()
    num_done = 0
    try:
        f = open(export.filename, "w")

        try:
            f.write(Purchase.csvheader() + "\n")
            for user in User.objects.all():
                purchases = Purchase.objects.filter(user=user).filter(product__in=PRODUCTS).filter(date__gte=export.start).filter(date__lt=export.end)
                merged = {}
                for purchase in purchases:
                    num_done += 1
                    if num_done % 100 == 0:
                        export.progress = num_done * 100 / num_todo
                        export.save()
                    f.write(purchase.csv() + "\n")
                    if purchase.valid:
                        if not purchase.product in merged:
                            merged[purchase.product] = 0
                        merged[purchase.product] += purchase.price

                purchases.delete()
                activity, created = Activity.objects.get_or_create(
                    name='Merged set',
                    note='Merged set between ' + export.start.strftime("%d-%m-%Y @ %H:%M") + ' and ' + export.end.strftime("%d-%m-%Y @ %H:%M"),
                    start=export.start,
                    end=export.end)

                for product, price in merged.items():
                    purchase = Purchase(
                        date=datetime.datetime.combine(export.start, datetime.time()), activity=activity, user=user, product=product, price=price, admin=True, valid=True, assoc_file='')
                    purchase.date = export.start
                    purchase.save()
        finally:
                f.close()
    except IOError:
        pass
    export.done = True
    export.save()

@ajax_required
@staff_member_required
def admin_credit_commit_batch(request):
    batch = request.POST['file']
    newentries = 0
    oldentries = 0
    nonkast = 0
    for line in batch.split('\n'):
        if line == '':
            continue
        items = re.findall(r'"(.*?)"[,$]*', line)
        #"3901","2013-03-12 12:12:04","2013-03-27 16:28:39","0691557066990","550","Incassobatch Maart 2013","1 kruisje kopen via kast","Foetsie","Sander Feringa","Verlengde Hereweg 61A","Groningen","8859903","26"
        #0           1                       2                   3            4              5                           6                   7           8               9                   10          11      12
        print items
        #            'omschrijving': str(amount) + " kruisjes, key:" + credit_key,
        print items[6]
        note = re.match(r'^[0-9]+ kruisjes, key:(([0-9]+):[0-9]+)$', items[6])
        if (not note) or (not items[7] == 'Foetsie'):
            nonkast += 1
            continue
        else:
            debit_id = items[0]
            date = datetime.datetime.strptime(items[1], "%Y-%m-%d %H:%M:%S")
            credit = -(int(items[4])*100) / int(EXCHANGE*100)
            credit /= 100
            name = items[8]
            bank_account = items[11]
            batch = int(items[12])

            user = User.objects.filter(name=name).filter(bank_account=bank_account)
            if (len(user) == 0):
                return HttpResponse(status=409, content='Error: User with name ' + name + ' and bank account ' + bank_account + ' was not found. Check for errors and retry. I have successfully imported ' + str(newentries) + ', ignored ' + str(nonkast) + ' non-kast entries,  and skipped ' + str(oldentries) + ' entries that were previously imported.')
            elif (len(user) > 1):
                return HttpResponse(status=409, content='Error: Multiple users with name ' + name + ' and bank account ' + bank_account + ' were found. Check for errors and retry. I have successfully imported ' + str(newentries) + ', ignored ' + str(nonkast) + ' non-kast entries,  and skipped ' + str(oldentries) + ' entries that were previously imported.')
            else:
                if Signed_debit.objects.filter(purchase__credit_key=note.group(1)).exists():
                    oldentries += 1
                    continue
                else:
                    if note.group(2) == str(user[0].pk):
                        try:
                            print user[0]
                            print note.group(1)
                            purchase = Purchase.objects.filter(user=user[0]).get(credit_key=note.group(1)) # superfluous filter, ensures no funny business changing the user of a debit.
                            if purchase.price != credit:
                                return HttpResponse(status=409, content='Error, number of credits does not match. Expected: ' + str(purchase.price) + ', got: ' + str(credit))
                            Signed_debit(debit_id=debit_id, user=user[0], date=date, batchnumber=batch, purchase=purchase).save()
                            newentries += 1
                        except Purchase.MultipleObjectsReturned:
                            return HttpResponse(status=409, content='Error, multiple purchases with the id ' + note.group(1) + ' exist. This should never happen and indicates multiple instantaneous purchases by a single user ' + user[0].name + '.')
                        except Purchase.DoesNotExist:
                            return HttpResponse(status=409, content='Error, purchase with user ' + user[0].name + ' and key ' + note.group(1) + ' does not exist. Check for errors and retry. I have successfully imported ' + str(newentries) + ', ignored ' + str(nonkast) + ' non-kast entries,  and skipped ' + str(oldentries) + ' entries that were previously imported.')        
                    else:
                        return HttpResponse(status=409, content='Error: User PK does not match, found: ' + note.group(2) + ', expected ' + str(user[0].pk) + '(' + user[0].name + ')' + '.')
    return HttpResponse(status=200, content='Successfully imported ' + str(newentries) + ' entries. Skipped ' + str(oldentries) + ' that were previously imported, ignored ' + str(nonkast) + ' entries not from kast.')


@ajax_required
@staff_member_required
def admin_credit_batch_list(request):
    batches = set()
    debits = Signed_debit.objects.all()
    for debit in debits:
        batches.add(debit.batchnumber)

    return render_to_response('admin/credit/batch_options.html', {'batches': batches}, context_instance=RequestContext(request))


@ajax_required
@staff_member_required
def admin_credit_batch(request):
    debits = Signed_debit.objects.filter(batchnumber=request.GET['batch'])
    resp = []
    for debit in debits:
        resp.append({
            'pk': debit.pk,
            'debit_id': debit.debit_id,
            'user': debit.user.name,
            'credits': debit.purchase.price,
            'key': debit.purchase.credit_key,
            'date': debit.date.strftime('%d/%m/%Y %H:%M'),
            'valid': debit.valid,
        })

    resp = list(reversed(sorted(resp, key=lambda debit: debit['debit_id'])))

    return HttpResponse(status=200, content=json.dumps(resp))


@ajax_required
@staff_member_required
def admin_credit_load_status(request):
    user_list = []
    for user in User.objects.filter(active=True):
        debits = Signed_debit.objects.filter(user=user)
        purcs = Purchase.objects.filter(user=user).filter(product__in=CREDITS)

        # valid signed debits with corresponding valid purchases
        correct_qset = debits.exclude(valid=False).exclude(purchase__valid=False)

        signed_purcs = [debit.purchase for debit in correct_qset]
        # valid purchases without corresponding signed debit (paying too little)
        unsigned_purcs = [p for p in purcs if p not in signed_purcs and p.valid]

        # valid signed debits without corresponding purchase (paying too much)
        wrongly_signed = debits.exclude(valid=False).filter(purchase__valid=False)

        unsigned = -sum([p.price for p in unsigned_purcs])
        wrongly = -sum([debit.purchase.price for debit in wrongly_signed])
        total = unsigned - wrongly
        user_list.append({'user': user.name, 'unsigned': unsigned, 'wrongly': wrongly, 'total': total})

    user_list = sorted(user_list, key=lambda instance: instance['total'])
    paginator = Paginator(user_list, 20)

    users = None
    try:
        page = request.GET['page']
        users = paginator.page(page)
    except (PageNotAnInteger, KeyError):
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)

    return render_to_response('admin/credit/userlist.html', {"users": users})


@ajax_required
@staff_member_required
def admin_credit_invalidate(request):
    req = Signed_debit.objects.get(pk=request.POST['debit'])
    print request.POST['valid']
    req.valid = True if request.POST['valid'] == 'true' else False
    req.save()
    resp = {'debit': request.POST['debit'], 'valid': 'false' if request.POST['valid'] == 'true' else 'true'}
    resp['textstatus'] = 'Make invalid' if resp['valid'] == 'false' else 'Make valid'
    return HttpResponse(status=200, content=json.dumps(resp))
