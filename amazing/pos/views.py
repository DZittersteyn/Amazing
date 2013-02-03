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
import datetime
import json
import threading

from pos.models import *


def ajax_required(f):
    def wrap(request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()
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
            bcauth = 'barcode' in request.REQUEST and user.barcode != "" and request.REQUEST['barcode'] == user.barcode
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
    if user == None:
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
            if user.buy_item(request.POST['productID'], amount, activity, request.user.is_staff):
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
                                Activity.objects.filter(end=None).exclude(start=None).order_by('-start'),
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
    active = list(chain(Activity.objects.filter(end=None).exclude(start=None).order_by('-start'), [Activity.get_normal_sale()]))
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
def admin_undo_dialog(request):
    user_id = request.GET['user']
    purchases = Purchase.objects.filter(user=user_id).order_by('-date')
    user_name = User.objects.get(pk=user_id).name
    return render_to_response("undodialog.html", {'user_name': user_name, 'user_id': user_id, 'purchases': purchases, 'purchases_old': None, 'admin': True}, context_instance=RequestContext(request))


@staff_member_required
@ajax_required
def admin_exportcontent(request):
    purchases = Purchase.objects.all()
    for purchase in purchases:
        # i hate date arithmetic.

        # equals (purchase.date.month + 1) - 1 % 12 + 1.
        nextmonth = purchase.date.month % 12 + 1

        # if month = 1 we passed the year border.
        nextyear = purchase.date.year + (1 if nextmonth == 1 else 0)

        start = datetime.date(year=purchase.date.year, month=purchase.date.month, day=1)
        end = datetime.date(year=nextyear, month=nextmonth, day=1)
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
        if export.end > datetime.date.today():
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


@staff_member_required
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


@staff_member_required
@ajax_required
def systemuser(request):
    pass
