from django.shortcuts import render_to_response

from django.template import RequestContext

from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect

from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.contrib.admin.views.decorators import staff_member_required

from django.core.servers.basehttp import FileWrapper

from itertools import chain
from operator import itemgetter
import datetime
import json
import threading
import HTMLParser

from pos.models import *


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


@login_required
@ajax_required
def passcode(request):
    return render_to_response("passcode.html", context_instance=RequestContext(request))


@login_required
@ajax_required
def noCredit(request):
    return render_to_response("noCredit.html", context_instance=RequestContext(request))


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

    return render_to_response("filtereduserlist.html", {'filter': beginswith, 'users': users})


@login_required
@ajax_required
def userlist(request):
    filters = []

    a = ord('a')
    for l in range(0, 25, 2):
        filters.append("".join((chr(l + a), chr(l + a + 1))))

    return render_to_response("userlist.html", {'filters': filters}, context_instance=RequestContext(request))


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
            if user.buy_item(category, amount, activity, request.user.is_staff):
                return HttpResponse(status=200)
            else:
                return HttpResponse(status=409, content='Insufficient credit')


def admin(request):
    if request.user.is_staff:
        return render_to_response('admin.html', context_instance=RequestContext(request))
    else:
        return HttpResponse(status=401, content="You are not admin. Log in via /pos/login.html")


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

    resp['user'] = user.as_dict()
    resp['activities'] = activities

    return render_to_response('admin/user/user_options.html', resp,
                              context_instance=RequestContext(request))


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
    [p, c] = admin_purchase_qset_to_dict(purchases)
    res['products'] = p
    res['credits'] = c
    res['user'] = request.REQUEST['user']
    print res
    return res


def admin_purchase_qset_to_dict(purchase_qset):
    p = {}

    for prod in PRODUCTS.keys():
        p[prod] = {'number': 0, 'desc': PRODUCTS[prod]['desc']}

    c = {}
    for cred in CREDITS.keys():
        c[cred] = {'number': 0, 'desc': CREDITS[cred]['desc']}

    for purchase in purchase_qset:
        if purchase.product in PRODUCTS:
            p[purchase.product]['number'] += purchase.price
        if purchase.product in CREDITS:
            c[purchase.product]['number'] -= purchase.price

    return [p, c]


@staff_member_required
@ajax_required
def admin_activity_list(request):
    invalid = Activity.objects.filter(end=None).filter(start=None).exclude(pk=Activity.get_normal_sale().pk)
    active = list(chain(Activity.objects.filter(end=None).exclude(start=None).order_by('-start').exclude(pk=Activity.get_normal_sale().pk), [Activity.get_normal_sale()]))
    done = Activity.objects.exclude(end=None).order_by('-end')
    return render_to_response('admin/activity/activity_list.html', {'invalid': invalid, 'active': active, 'done': done}, context_instance=RequestContext(request))


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
    [p, c] = admin_purchase_qset_to_dict(purchases)
    return render_to_response('admin/activity/activity_content.html', {'activity': activity, 'products': p, 'credits': c}, context_instance=RequestContext(request))


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


@staff_member_required
@ajax_required
def admin_totals_result(request):
    # Yes. This is freaking long and complicated. I screwed up, sorry. It works though, and I'm not going to screw with it for now.
    # Have a bunny to cheer you up:

    # (~\       _
    #  \ \     / \   Sorry!
    #   \ \___/ /\\  /
    #    | , , |  ~
    #    ( =v= )
    #     ` ^ '

    start = Inventory_balance.objects.get(pk=request.GET['from'])
    end = Inventory_balance.objects.get(pk=request.GET['to'])
    relevant_balances = Inventory_balance.objects.filter(date__range=(start.date, end.date)).order_by('date')

    balance = {}
    balance[start.date] = sum([a.modification for a in Inventory_balance_product.objects.filter(inventory=start).filter(category__in=PRODUCTS)])
    loss = {}
    loss[start.date] = 0

    credits = {}
    credits[start.date] = sum([a.modification for a in Inventory_balance_product.objects.filter(inventory=start).filter(category__in=CREDITS)])
    unsigned = {}
    unsigned[start.date] = 0

    labels = []

    current_bala = balance[start.date]
    current_loss = 0
    current_cred = credits[start.date]
    current_unsi = 0
    for balance_ind in range(0, len(relevant_balances)-1):

        labels.append({
            'series': 'Inventory',
            'x': relevant_balances[balance_ind].date.strftime("%Y-%m-%d %H:%M:%S"),
            'shortText': 'B',
            'text': relevant_balances[balance_ind].description
        })

        product_changes = {}
        credit_changes = {}
        relevant_user_purchases = Purchase.objects.filter(date__gte=relevant_balances[balance_ind].date).exclude(date__gte=relevant_balances[balance_ind+1].date)

        for user_purchase in relevant_user_purchases:
            if user_purchase.valid:
                if user_purchase.product in PRODUCTS:
                    if not user_purchase.date in product_changes:
                        product_changes[user_purchase.date] = -user_purchase.price
                    else:
                        product_changes[user_purchase.date] -= user_purchase.price
                elif user_purchase.product in CREDITS:
                    if not user_purchase.date in credit_changes:
                        credit_changes[user_purchase.date] = -user_purchase.price
                    else:
                        credit_changes[user_purchase.date] -= user_purchase.price

        relevant_purchases = Inventory_purchase.objects.filter(date__gte=relevant_balances[balance_ind].date).exclude(date__gte=relevant_balances[balance_ind+1].date)

        for inventory in relevant_purchases:
            relevant_purchase_producs = Inventory_purchase_product.objects.filter(inventory=inventory)
            for purchase in relevant_purchase_producs:
                if not inventory.date in product_changes:
                    product_changes[inventory.date] = purchase.modification
                else:
                    product_changes[inventory.date] += purchase.modification

        for key in sorted(product_changes.keys()):
            current_bala += product_changes[key]
            balance[key] = current_bala
            loss[key] = current_loss

        new_bala = sum([a.modification for a in Inventory_balance_product.objects.filter(inventory=relevant_balances[balance_ind+1]).filter(category__in=PRODUCTS)])
        current_loss += current_bala - new_bala
        current_bala = new_bala

        loss[relevant_balances[balance_ind+1].date] = current_loss
        balance[relevant_balances[balance_ind+1].date] = current_bala

        for key in sorted(credit_changes.keys()):
            current_cred += credit_changes[key]
            credits[key] = current_cred
            unsigned[key] = current_unsi

        new_cred = sum([a.modification for a in Inventory_balance_product.objects.filter(inventory=relevant_balances[balance_ind+1]).filter(category__in=CREDITS)])
        current_unsi += current_cred - new_cred
        current_cred = new_cred

        credits[relevant_balances[balance_ind+1].date] = current_cred
        unsigned[relevant_balances[balance_ind+1].date] = current_unsi

    labels.append({
        'series': 'Inventory',
        'x': relevant_balances[len(relevant_balances)-1].date.strftime("%Y-%m-%d %H:%M:%S"),
        'shortText': 'B',
        'text': relevant_balances[len(relevant_balances)-1].description
    })


    purchase_keys = sorted(set(balance.keys() + loss.keys()))
    purchase_graph = ['"Date,Inventory,Loss \\n"']
    for key in purchase_keys:
        print key
        balance_val = balance[key] if key in balance else ''
        loss_val = loss[key] if key in loss else ''
        purchase_graph += ['"' + (', '.join([key.strftime("%Y-%m-%d %H:%M:%S"), str(balance_val), str(loss_val)])) + '\\n"']

    credit_keys = sorted(set(credits.keys() + unsigned.keys()))
    credit_graph = ['"Date,Credits,Unsigned \\n"']
    for key in credit_keys:
        balance_val = credits[key] if key in credits else ''
        loss_val = unsigned[key] if key in unsigned else ''
        credit_graph += ['"' + (', '.join([key.strftime("%Y-%m-%d %H:%M:%S"), str(balance_val), str(loss_val)])) + '\\n"']

    print json.dumps(labels)
    return render_to_response('admin/totals/totals_detail.html', {
        'purchase_graph': '+ \n'.join(purchase_graph),
        'credit_graph': '+\n'.join(credit_graph),
        'labels': json.dumps(labels)
    }, context_instance=RequestContext(request))







@staff_member_required
@ajax_required
def admin_inventory_total(request):
    prods, creds, unkns = inventory_totals()
    return render_to_response('admin/inventory/inventory_total.html', {'products': prods, 'credits': creds, 'unknown': unkns}, context_instance=RequestContext(request))


def inventory_totals():
    last_balance = None
    try:
        last_balance = Inventory_balance.objects.latest(field_name='date')
    except Inventory_balance.DoesNotExist:
        last_balance = Inventory_balance(description='Initial empty balance')
        last_balance.save()
        for product in PRODUCTS:
            Inventory_balance_product(inventory=last_balance, category=product, modification=0).save()
        for credit in CREDITS:
            Inventory_balance_product(inventory=last_balance, category=credit, modification=0).save()
    last_balance_items = Inventory_balance_product.objects.filter(inventory=last_balance)
    relevant_purchases = Inventory_purchase.objects.filter(date__gte=last_balance.date)
    relevant_user_purchases = Purchase.objects.filter(date__gte=last_balance.date)

    prods = {}
    creds = {}
    unkns = {}

    for item in PRODUCTS:
        prods[item] = {'desc': PRODUCTS[item]['desc'], 'val': 0}
    for item in CREDITS:
        creds[item] = {'desc': CREDITS[item]['desc'], 'val': 0}

    for entry in last_balance_items:
        print entry
        if entry.category in PRODUCTS:
            prods[entry.category] = {'desc': PRODUCTS[entry.category]['desc'], 'val': entry.modification}
        elif entry.category in CREDITS:
            creds[entry.category] = {'desc': CREDITS[entry.category]['desc'], 'val': entry.modification}
        else:
            unkns[entry.category] = {'desc': entry.category, 'val': entry.modification}

    for entry in relevant_purchases:
        relevant_purchase_entries = Inventory_purchase_product.objects.filter(inventory=entry)
        for purchase in relevant_purchase_entries:
            if purchase.category in prods:
                prods[purchase.category]['val'] += purchase.modification
            elif purchase.category in creds:
                creds[purchase.category]['val'] += purchase.modification
            else:
                if not purchase.category in unkns:
                    unkns[purchase.category]['val'] = 0
                unkns[purchase.category]['val'] += purchase.modification

    for user_purchase in relevant_user_purchases:
        if user_purchase.valid:
            if user_purchase.product in prods:
                prods[user_purchase.product]['val'] -= user_purchase.price
            elif user_purchase.product in creds:
                creds[user_purchase.product]['val'] -= user_purchase.price
            else:
                if not user_purchase.product in unkns:
                    unkns[user_purchase.product]['val'] = 0
                    unkns[user_purchase.product]['desc'] = user_purchase.product
                unkns[user_purchase.product]['val'] -= user_purchase.price

    print prods
    print creds
    print unkns
    return prods, creds, unkns


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

    prods, creds, unkns = inventory_totals()

    for product in prods:
        if product in request.POST:
            mod = int(request.POST[product]) - prods[product]['val']
            if mod != 0:
                Inventory_balance_product(inventory=inv, category=product, modification=mod).save()
    for credit in creds:
        if credit in request.POST:
            mod = int(request.POST[credit]) - creds[credit]['val']
            if mod != 0:
                Inventory_balance_product(inventory=inv, category=credit, modification=mod).save()
    for unknown in unkns:
        if unknown in request.POST:
            mod = int(request.POST[unknown]) - unkns[unknown]['val']
            if mod != 0:
                Inventory_balance_product(inventory=inv, category=product, modification=mod).save()

    return HttpResponse(status=200, content='New balance created')


@staff_member_required
@ajax_required
def admin_inventory_purchase(request):
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
                purchases = Purchase.objects.filter(user=user).filter(date__gte=export.start).filter(date__lt=export.end)
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
                    name='Merged ' + export.start.strftime("%m-%y"),
                    start=datetime.datetime.combine(export.start, datetime.time()),
                    end=datetime.datetime.combine(export.end, datetime.time()))

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
