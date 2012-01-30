from django.shortcuts import render_to_response, get_object_or_404
from pos.models import User
from django.template import RequestContext
from django.db.models.query import ValuesListQuerySet
from django.http import HttpResponse
from django.core import serializers


def index(request):
	filters = []
	users = User.objects.all()

	a = ord('a')
	for l in range(0,25,2):
		filters.append((chr(l + a), chr(l + a + 1)))
	
	lists = []
	for filter in filters:
		lists.append(("".join(filter),[user for user in users if user.name.lower().startswith(filter)]))

	return render_to_response("pos/userselect.html", {'lists': lists}, context_instance=RequestContext(request))

def default(o):
	if isinstance(o, ValuesListQuerySet):
		return list(o)
	raise TypeError(repr(o) + " is not JSON serializable")

def user(request, user_id):
	user = User.objects.filter(pk=user_id)
	print user

	JSONSerializer = serializers.get_serializer("json")
	json_serializer = JSONSerializer()
	json_serializer.serialize(user)
	print json_serializer
	print type(json_serializer.getvalue())
	data = json_serializer.getvalue()

	if request.is_ajax():
		return render_to_response("pos/user.json", {'user': data});
	else:
		return render_to_response("pos/user.json", {'user': data});
		#return HttpResponse(status=400);




