from django.shortcuts import render_to_response, get_object_or_404
from pos.models import *
from django.template import RequestContext
from django.db.models.query import ValuesListQuerySet
from django.http import HttpResponse
from django.core import serializers
from django.core.context_processors import csrf


def index(request):
	c = RequestContext(request)
	c.update(csrf(request))
	return render_to_response("pos/userselect.html", c)

def noCredit(request):
	return render_to_response("pos/noCredit.html", context_instance=RequestContext(request))

def buyLine(request):
	return render_to_response("pos/buyLine.html", context_instance=RequestContext(request))

def purchaselist(request, user_id):
	purchases = Purchase.objects.filter(user=user_id).order_by('-date')

	return render_to_response("userdetails.html", {'purchases': purchases, 'map': PRODUCTS}, context_instance=RequestContext(request))

def undoDialog(request, user_id):
	purchases = Purchase.objects.filter(user=user_id).order_by('-date')
	return render_to_response("undodialog.html", {'user_id': user_id, 'purchases': purchases})


def newUser(request):
	return render_to_response("pos/newUser.html", context_instance=RequestContext(request))

def filtereduserlist(request, beginswith):
	users = []
	for char in beginswith:
		users.extend(User.objects.filter(name__startswith=char).order_by('name'))

	return render_to_response("pos/filtereduserlist.html", {'beginswith':beginswith, 'users': users})

def userlist(request):
	filters = []

	a = ord('a')
	for l in range(0,25,2):
		filters.append("".join((chr(l + a), chr(l + a + 1))))

	return render_to_response("pos/userlist.html", {'filters': filters}, context_instance=RequestContext(request))

def user_edit(request):
	if request.is_ajax():
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
	else:
		return HttpResponse(status=400, content='non-ajax request not supported')

def user(request, user_id):
	if request.is_ajax():
		user = User.objects.get(pk=user_id)
		if user == None:
			return HttpResponse(status=404)
		if request.method == 'GET':
			JSONSerializer = serializers.get_serializer("json")
			json_serializer = JSONSerializer()
			json_serializer.serialize([user])
			data = json_serializer.getvalue()
			return HttpResponse(data, mimetype='application/json')
		elif request.method == 'POST':
			if request.POST['type'] == 'credit':
				if user.buy_credit(request.POST['credittype'], int(request.POST['amount']) ):
					return HttpResponse(status=200)
				else:
					return HttpResponse(status=409, content='Incorrect credit type')
			elif request.POST['type'] == 'product':
				if user.buy_item(request.POST['productID']):
					return HttpResponse(status=200)
				else:
					return HttpResponse(status=409, content='Insufficient credit')
	else:
		return HttpResponse(status=400, content='non-ajax request not supported')




