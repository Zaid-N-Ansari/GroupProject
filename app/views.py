from django.shortcuts import render
from ProChat.settings import DEBUG

_DEBUG_ = False

def home_screen_view(request):
	context = {}
	context['debug_mode'] = DEBUG
	context['debug'] = _DEBUG_
	context['room_id'] = 2
	return render(request, 'app/home.html', context)
