from django.shortcuts import render_to_response, get_object_or_404
from pos.models import User

def index(request):
	filters = []
	users = User.objects.all()

	a = ord('a')
	for l in range(0,25,2):
		filters.append((chr(l + a), chr(l + a + 1)))
	
	lists = []
	for filter in filters:
		lists.append(("".join(filter),[user for user in users if user.name.lower().startswith(filter)]))

	return render_to_response("pos/userselect.html", {'lists': lists})
