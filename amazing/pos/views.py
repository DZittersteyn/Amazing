from django.shortcuts import render_to_response, get_object_or_404
from pos.models import User
from django.template import RequestContext
from django.db.models.query import ValuesListQuerySet
from django.http import HttpResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt

def index(request):
	return render_to_response("pos/userselect.html", context_instance=RequestContext(request))



def userlist(request):
	filters = []
	users = User.objects.all()

	a = ord('a')
	for l in range(0,25,2):
		filters.append((chr(l + a), chr(l + a + 1)))

	lists = []
	for filter in filters:
		lists.append(("".join(filter),[user for user in users if user.name.lower().startswith(filter)]))
	
	return render_to_response("pos/userlist.html", {'lists': lists}, context_instance=RequestContext(request))


@csrf_exempt
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
		return HttpResponse(status=400)




