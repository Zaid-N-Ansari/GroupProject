from enum import unique
from django.db import models
from ProChat.settings import AUTH_USER_MODEL

class ChatPrivateRoom(models.Model):
	user1 = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user1')
	user2 = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user2')
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return str(self.id)
	
	@property
	def group_name(self):
		return f'ChatPrivateRoom{self.id}'


class ChatRoomMessageManager(models.Manager):
	def by_room(self, room):
		query_set = ChatRoomMessage.objects.filter(room=room).order_by('-timestamp')
		return query_set


class ChatRoomMessage(models.Model):
	user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
	room = models.ForeignKey(ChatPrivateRoom, on_delete=models.CASCADE)
	timestamp = models.DateTimeField(auto_now_add=True)
	content = models.TextField(unique=False, blank=False)

	objects = ChatRoomMessageManager()

	def __str__(self):
		return self.content
