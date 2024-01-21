from django.db import models
from ProChat.settings import AUTH_USER_MODEL


class ChatPublicRoom(models.Model):
	title = models.CharField(max_length=60, unique=True, blank=False)
	users = models.ManyToManyField(AUTH_USER_MODEL, blank=True, help_text='users connected to chat')


	def __str__(self):
		return self.title
	
	def connect_user(self, user):
		is_user_added = False
		if not user in self.users.all():
			self.users.add(user)
			self.save()
			is_user_added = True
		
		elif user in self.users.all():
			is_user_added = True
	
		return is_user_added


	def disconnect_user(self, user):
		is_user_removed = False
		if user in self.users.all():
			self.users.remove(user)
			self.save()
			is_user_removed = True

		return is_user_removed


	@property
	def group_name(self):
		return f'ChatPublicRoom-{self.id}'
	


class ChatPublicRoomMessageManager(models.Manager):
	def by_room(self, room):
		query_set = ChatPublicRoomMessage.objects.filter(room=room).order_by('-timestamp')

		return query_set


class ChatPublicRoomMessage(models.Model):
	user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
	room = models.ForeignKey(ChatPublicRoom, on_delete=models.CASCADE)
	timestamp = models.DateTimeField(auto_now_add=True)
	content = models.TextField(unique=False, blank=False)


	objects = ChatPublicRoomMessageManager()


	def __str__(self):
		return self.content
