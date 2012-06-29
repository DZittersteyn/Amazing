from django.shortcuts import render_to_response, get_object_or_404
from pos.models import *
from django.template import RequestContext
from django.db.models.query import ValuesListQuerySet
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.core import serializers
from django.core.context_processors import csrf
from django.contrib import auth 
from django.contrib.auth.decorators import login_required
import datetime

def ajax_required(f):
	def wrap(request, *args, **kwargs):
			if not request.is_ajax():
				return HttpResponseBadRequest()
			return f(request, *args, **kwargs)
	
	wrap.__doc__=f.__doc__
	wrap.__name__=f.__name__
	return wrap

def login(request):
	if request.method == 'GET':
		return render_to_response("login.html",{'retry': 'retry' in request.GET, 'next': request.GET.get('next')},context_instance=RequestContext(request))
	elif request.method =='POST':
		username = request.POST['username']
		password = request.POST['password']
		user = auth.authenticate(username=username, password=password)
		if user is not None and user.is_active:
			auth.login(request, user)
			return HttpResponseRedirect(request.POST.get('next', default="."))
		else:
			return render_to_response("login.html",{'retry': True, 'next': request.GET.get('next')},context_instance=RequestContext(request))
	else:
		return HttpResponse(status=400, content='Unknown method')

@login_required
def logout(request):
	auth.logout(request)
	return HttpResponseRedirect("login.html")

@login_required
def index(request):
	c = RequestContext(request)
	c.update(csrf(request))
	return render_to_response("pos/userselect.html", {'activity': Activity.get_active()}, c)


@ajax_required
def passcode(request):
	return render_to_response("pos/passcode.html",context_instance=RequestContext(request))

@ajax_required
def noCredit(request):
	return render_to_response("pos/noCredit.html", context_instance=RequestContext(request))

@ajax_required
def buyLine(request):
	return render_to_response("pos/buyLine.html", context_instance=RequestContext(request))

@ajax_required
def transaction(request, tr_id):
	if request.method == 'POST':
		transaction = Purchase.objects.get(pk=tr_id)
		price = 0
		try:
			price = PRODUCTS[transaction.product]['price']
		except KeyError:
			try:
				price = CREDITS[transaction.product]['price']
			except KeyError:
				return HttpResponse(status=400, content='Unknown product');
		if request.POST['valid'] == 'true':
			if transaction.valid == 0:
				if transaction.user.credit >= price :
					transaction.valid = 1
					transaction.user.credit -= price
					transaction.save()
					transaction.user.save()
					return HttpResponse(status=200)
				else:
					return HttpResponse(status=409, content='not enough credits')
			else:
				return HttpResponse(status=400, content='trying to redo a valid transaction')
		elif request.POST['valid'] == 'false':
			if transaction.valid == 1:
				if transaction.user.credit >= -price :
					transaction.valid = 0
					transaction.user.credit += price
					transaction.save()
					transaction.user.save()
					return HttpResponse(status=200)
				else:
					return HttpResponse(status=409, content='not enough credits')
			else:
				return HttpResponse(status=400, content='trying to redo a valid transaction')
		else:
			return HttpResponse(status=400, content='mode unsupported')
	else:
		return render_to_response("transactionli.html", {'purchase': Purchase.objects.get(pk=tr_id)}, context_instance=RequestContext(request))



@ajax_required
def purchaselist(request, user_id):
	purchases = Purchase.objects.filter(user=user_id).order_by('-date')[:20]

	return render_to_response("userdetails.html", {'purchases': purchases, 'map': PRODUCTS}, context_instance=RequestContext(request))

@ajax_required
def undoDialog(request, user_id):
	cutoff = datetime.datetime.now() - datetime.timedelta(hours=2)
	purchases = Purchase.objects.filter(user=user_id).order_by('-date').exclude(date__lte=cutoff)
	purchases_old = Purchase.objects.filter(user=user_id).order_by('-date').exclude(date__gt=cutoff)
	user_name = User.objects.get(pk=user_id).name;
	return render_to_response("undodialog.html", {'user_name': user_name ,'user_id': user_id, 'purchases': purchases, 'purchases_old': purchases_old}, context_instance=RequestContext(request))


@ajax_required
def newUser(request):
	return render_to_response("pos/newUser.html", context_instance=RequestContext(request))

@ajax_required
def filtereduserlist(request, beginswith):
	users = []
	for char in beginswith:
		users.extend(User.objects.filter(name__startswith=char).order_by('name'))

	return render_to_response("pos/filtereduserlist.html", {'beginswith':beginswith, 'users': users})

@ajax_required
def userlist(request):
	filters = []

	a = ord('a')
	for l in range(0,25,2):
		filters.append("".join((chr(l + a), chr(l + a + 1))))

	return render_to_response("pos/userlist.html", {'filters': filters}, context_instance=RequestContext(request))

@ajax_required
def user_edit(request):
	if request.method == 'POST':
		if request.POST['mode'] == 'new':
			u=User(
				name=request.POST['name'],
				address=request.POST['address'],
				city=request.POST['city'],
				bank_account=request.POST['bank_account'],
				email=request.POST['email'],
				barcode=request.POST['barcode'],
				credit=0,
				has_passcode=request.POST['has_passcode'],
				passcode=request.POST['passcode']
				)
			u.save()
			return HttpResponse(status=200, content=u.pk)
		elif request.POST['mode'] == 'edit':
			u = User.objects.get(pk=request.POST['pk'])
			u.name=request.POST['name']
			u.address=request.POST['address']
			u.city=request.POST['city']
			u.bank_account=request.POST['bank_account']
			u.email=request.POST['email']
			u.barcode=request.POST['barcode']
			print('-----------------------------------')
			print(request.POST['has_passcode'])
			print('-----------------------------------')
			u.has_passcode= True if request.POST['has_passcode'] == "True" else False
			print(u.has_passcode)
			u.passcode=request.POST['passcode']
			u.save()
			u = User.objects.get(pk=request.POST['pk'])
			print(u.has_passcode)
			return HttpResponse(status=200, content=u.pk)		
		else:
			return HttpResponse(status=400, content='mode unsupported')
	else:
		return HttpResponse(status=400, content='GET not supported, use user/id')

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
		return user(request, u.pk)
	else:
		return HttpResponse(status=400, content="no barcode submitted")

@ajax_required
def user(request, user_id):
	user = User.objects.get(pk=user_id)
	if user == None:
		return HttpResponse(status=404, content="user does not exist")
	if request.method == 'GET':
		if not (user.barcode != "" and 'barcode' in request.GET and user.barcode == request.GET['barcode']):
			if user.has_passcode and 'passcode' in request.GET and (user.passcode != request.GET['passcode']):
				return HttpResponse(status=401)
		JSONSerializer = serializers.get_serializer("json")
		json_serializer = JSONSerializer()
		user.password = "blocked"
		json_serializer.serialize([user])
		data = json_serializer.getvalue()
		return HttpResponse(data, mimetype='application/json')
	elif request.method == 'POST':
		if request.POST['type'] == 'credit':
			if user.buy_credit(request.POST['credittype'], CREDITS[request.POST['credittype']]['price'], int(request.POST['amount']) ):
				return HttpResponse(status=200)
			else:
				return HttpResponse(status=409, content='Incorrect credit type')
		elif request.POST['type'] == 'product':
			if user.buy_item(request.POST['productID'], PRODUCTS[request.POST['productID']]['price']):
				return HttpResponse(status=200)
			else:
				return HttpResponse(status=409, content='Insufficient credit')
	

