from django.shortcuts import render_to_response, get_object_or_404
from pos.models import User

def index(request):
    users = User.objects.all()
    return render_to_response("pos/userselect.html", {'users': users})
