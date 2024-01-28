from itertools import chain
from django.shortcuts import redirect, render
from json import dumps
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from ProChat.settings import DEBUG
from account.models import ChatAccount
from .models import ChatPrivateRoom
from .utils import get_private_chat
from .exceptions import ClientError

_DEBUG_ = False

def private_chat_room_view(request, *args, **kwargs):
	user = request.user

	room_id = request.GET.get("room_id")
	
	context = {}
	if not user.is_authenticated:
		return redirect('login')
	

	if room_id:
		try:
			room = ChatPrivateRoom.objects.get(pk=room_id)
			context['room'] = room
		except ChatPrivateRoom.DoesNotExist as e:
			pass
	
	room1 = ChatPrivateRoom.objects.filter(user1=user, is_active=True)
	room2 = ChatPrivateRoom.objects.filter(user2=user, is_active=True)

	rooms = list(chain(room1, room2))

	m_and_f = []
	for room in rooms:
		if room.user1 == user:
			friend = room.user2
		else:
			friend = room.user1

		m_and_f.append({
			'message': '',
			'friend': friend
		})

	context['m_and_f'] = m_and_f
	context['debug'] = _DEBUG_
	context['debug_mode'] = DEBUG

	return render(request, 'chat/room.html', context)


def create_private_chat(request, *args, **kwargs):
	user1 = request.user
	payload = {}
	if user1.is_authenticated:
		if request.method == 'POST':
			user2_id = request.POST.get('user2_id')
			try:
				user2 = ChatAccount.objects.get(pk=user2_id)
				chat = get_private_chat(user1, user2)
				payload['response'] = 'Chat Retrieved'
				payload['chatroom_id'] = chat.id
			except ChatAccount.DoesNotExist:
				payload['response'] = 'Chat not Retrieved'
	else:
		payload['response'] = 'Authentication Required'

	return HttpResponse(dumps(payload), content_type='application/json')



