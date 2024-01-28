from .models import ChatPrivateRoom
from django.contrib.humanize.templatetags.humanize import naturalday
from datetime import datetime as dt, timezone as tz
from pytz import timezone

def get_private_chat(user1, user2):
	try:
		chat = ChatPrivateRoom.objects.get(user1=user1, user2=user2)
	except ChatPrivateRoom.DoesNotExist:
		try:
			chat = ChatPrivateRoom.objects.get(user1=user2, user2=user1)
		except ChatPrivateRoom.DoesNotExist:
			chat = ChatPrivateRoom(user1=user1, user2=user2)
			chat.save()


	return chat

def set_timestamp(timestamp):
	timestamp = timestamp.astimezone(timezone('Asia/Kolkata'))
	if naturalday(timestamp) == 'today' or naturalday(timestamp) == 'yesterday':
		str_time = dt.strftime(timestamp, '%I:%M %p')
		str_time = str_time.strip('0')
		ts = f'{naturalday(timestamp)} at {str_time}'
	else:
		str_time = dt.strftime(timestamp, '%d/%m/%Y')
		ts = f'{str_time}'

	return ts