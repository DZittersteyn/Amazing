from django.shortcuts import render_to_response
from pos.models import *
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.core import serializers
# from django.core.context_processors import csrf
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
import datetime


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
        if 'user' in request.REQUEST:
            user = User.objects.get(pk=request.REQUEST['user'])
            bcauth = 'barcode' in request.REQUEST and user.barcode != "" and request.REQUEST['barcode'] == user.barcode
            pcauth = (not user.has_passcode) or ('passcode' in request.REQUEST and request.REQUEST['passcode'] == user.passcode)
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
    return HttpResponseRedirect("login.html")


@login_required
def index(request):
    #c = RequestContext(request) #why did i do this? seems to work fine without.
    #c.update(csrf(request))

    return render_to_response("pos/userselect.html", {'activity': Activity.get_active(), 'mainuser': request.user.username}, context_instance=RequestContext(request))


@login_required
@ajax_required
def passcode(request):
    return render_to_response("pos/passcode.html", context_instance=RequestContext(request))


@login_required
@ajax_required
def noCredit(request):
    return render_to_response("pos/noCredit.html", context_instance=RequestContext(request))


@login_required
@ajax_required
def buyLine(request):
    return render_to_response("pos/buyLine.html", {'pieceprice': EXCHANGE}, context_instance=RequestContext(request))


@user_auth_required
@login_required
@ajax_required
def purchase(request):
    if request.method == 'POST':
        purchase = Purchase.objects.get(pk=request.POST['purchaseid'])
        price = purchase.price

        if request.POST['valid'] == 'true':
            if purchase.valid == 0:
                if purchase.user.credit >= price:
                    purchase.valid = 1
                    purchase.user.credit -= price
                    purchase.save()
                    purchase.user.save()

                    return render_to_response("transactionli.html", {'purchase': Purchase.objects.get(pk=request.POST['purchaseid'])}, context_instance=RequestContext(request))
                else:
                    return HttpResponse(status=409, content='not enough credits')
            else:
                return HttpResponse(status=400, content='trying to redo a valid purchase')
        elif request.POST['valid'] == 'false':
            if purchase.valid == 1:
                if purchase.user.credit >= -price:
                    purchase.valid = 0
                    purchase.user.credit += price
                    purchase.save()
                    purchase.user.save()

                    return render_to_response("transactionli.html", {'purchase': Purchase.objects.get(pk=request.POST['purchaseid'])}, context_instance=RequestContext(request))
                else:
                    return HttpResponse(status=409, content='not enough credits')
            else:
                return HttpResponse(status=400, content='trying to undo an invalid purchase')
        else:
            return HttpResponse(status=400, content='mode unsupported')
    else:
        return render_to_response("transactionli.html", {'purchase': Purchase.objects.get(pk=request.GET['purchaseid'])}, context_instance=RequestContext(request))


@login_required
@ajax_required
def purchaselist(request):
    purchases = Purchase.objects.filter(user=request.GET['user']).order_by('-date')[:20]

    return render_to_response("userdetails.html", {'purchases': purchases, 'map': PRODUCTS}, context_instance=RequestContext(request))


@user_auth_required
@login_required
@ajax_required
def undo_dialog(request):
    user_id = request.GET['user']
    cutoff = datetime.datetime.now() - datetime.timedelta(hours=2)
    purchases = Purchase.objects.filter(user=user_id).order_by('-date').exclude(date__lte=cutoff)
    purchases_old = Purchase.objects.filter(user=user_id).order_by('-date').exclude(date__gt=cutoff)[0:15]
    user_name = User.objects.get(pk=user_id).name
    return render_to_response("undodialog.html", {'user_name': user_name, 'user_id': user_id, 'purchases': purchases, 'purchases_old': purchases_old}, context_instance=RequestContext(request))


@login_required
@ajax_required
def newUser(request):
    return render_to_response("pos/newUser.html", context_instance=RequestContext(request))


@login_required
@ajax_required
def filtereduserlist(request):
    beginswith = request.GET['beginswith']
    users = []
    for char in beginswith:
        users.extend(User.objects.filter(name__startswith=char).extra(select={'lower_name': 'lower(name)'}).order_by('lower_name').filter(active=True))

    return render_to_response("pos/filtereduserlist.html", {'filter': beginswith, 'users': users})


@login_required
@ajax_required
def userlist(request):
    filters = []

    a = ord('a')
    for l in range(0, 25, 2):
        filters.append("".join((chr(l + a), chr(l + a + 1))))

    return render_to_response("pos/userlist.html", {'filters': filters}, context_instance=RequestContext(request))


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
                credit=0,
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
        JSONSerializer = serializers.get_serializer("json")
        json_serializer = JSONSerializer()
        user.password = "blocked"
        json_serializer.serialize([user])
        data = json_serializer.getvalue()
        return HttpResponse(data, mimetype='application/json')
    elif request.method == 'POST':
        if request.POST['type'] == 'credit':
            if user.buy_credit(request.POST['credittype'], int(request.POST['amount'])):
                return HttpResponse(status=200)
            else:
                return HttpResponse(status=500, content='Incassomatic returned an error')
        elif request.POST['type'] == 'product':
            if user.buy_item(request.POST['productID']):
                return HttpResponse(status=200)
            else:
                return HttpResponse(status=409, content='Insufficient credit')


@permission_required('pos.admin')
def admin(request):
    return render_to_response('admin.html', context_instance=RequestContext(request))


@permission_required('pos.admin')
def user_admin(request, user_id):
    user = User.objects.get(pk=user_id)
    if user.has_passcode:
        request.GET['passcode'] = user.passcode
    return user(request, user_id)


@permission_required('pos.admin')
def admin_user_options(request, user_id):
    user = User.objects.get(pk=user_id)
    purchases = Purchase.objects.filter(user=user)

    candybigcount = purchases.filter(product="CANDYBIG").count()
    candysmallcount = purchases.filter(product="CANDYSMALL").count()
    beercount = purchases.filter(product="BEER").count()
    cancount = purchases.filter(product="CAN").count()
    soupcount = purchases.filter(product="SOUP").count()
    breadcount = purchases.filter(product="BREAD").count()
    sausagecount = purchases.filter(product="SAUSAGE").count()
    bapaocount = purchases.filter(product="BAPAO").count()

    kruisjes_purchase = purchases.filter(product="DIGITAL")
    numkruisjes = 0
    for purchase in kruisjes_purchase:
        numkruisjes += purchase.price

    activities = Activity.objects.all()

    return render_to_response('admin_user_options.html', {'user': user,
        'candybigcount': candybigcount,
        'candysmallcount': candysmallcount,
        'beercount': beercount,
        'cancount': cancount,
        'soupcount': soupcount,
        'breadcount': breadcount,
        'sausagecount': sausagecount,
        'bapaocount': bapaocount,

        'kruisjes': -numkruisjes,
        'price': -numkruisjes * EXCHANGE,

        'activities': activities,
        }, context_instance=RequestContext(request))


@permission_required('pos.admin')
def admin_edit_user(request, user_id):
    user = User.objects.get(pk=user_id)


@permission_required('pos.admin')
def admin_user_deactivate(request, user_id):
    user = User.objects.get(pk=user_id)
    user.active = False
    user.save()
    return HttpResponse(status=200, content="User deactivated")


@permission_required('pos.admin')
def admin_user_activate(request, user_id):
    user = User.objects.get(pk=user_id)
    user.active = True
    user.save()
    return HttpResponse(status=200, content="User deactivated")


@permission_required('pos.admin')
def admin_user_list(request):
    users = User.objects.all().extra(select={'lower_name': 'lower(name)'}).order_by('lower_name')
    return render_to_response('admin_user_list.html', {'users': users}, context_instance=RequestContext(request))
