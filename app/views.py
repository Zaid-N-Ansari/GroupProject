from django.shortcuts import render
from ProChat.settings import DEBUG

def home_screen_view(request):
	context = {}
	context['debug_mode'] = DEBUG
	context['room_id'] = 2
	return render(request, 'app/home.html', context)
