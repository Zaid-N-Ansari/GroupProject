from django.db import models
from ProChat.settings import AUTH_USER_MODEL, BASE_URL
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from notification.models import Notification


class ChatPrivateRoom(models.Model):
	user1 = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user1')
	
	user2 = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user2')
	
	is_active = models.BooleanField(default=False)
	
	connected_users = models.ManyToManyField(AUTH_USER_MODEL, blank=True, related_name='connected_users')

	def connect_user(self, user):
		is_user_added = False
		if not user in self.connected_users.all():
			self.connected_users.add(user)
			is_user_added = True
		return is_user_added

	def disconnect_user(self, user):
		is_user_removed = False
		if user in self.connected_users.all():
			self.connected_users.remove(user)
			is_user_removed = True
		return is_user_removed
	

	@property
	def group_name(self):
		return f'ChatPrivateRoom-{str(self.id)}'


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


class UnseenChatRoomMessages(models.Model):
	room = models.ForeignKey(ChatPrivateRoom, on_delete=models.CASCADE, related_name='room')
	
	user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
	
	count = models.IntegerField(default=0)
	
	most_recent_message = models.CharField(max_length=500, blank=True, null=True)
	
	reset_ts = models.DateTimeField()

	notifications = GenericRelation(Notification)

	def __str__(self):
		return f'{str(self.user.username)} has not seen messages'
	
	def save(self, *args, **kwargs):
		if not self.id:
			self.reset_ts = timezone.now()
		return super(UnseenChatRoomMessages, self).save(*args, **kwargs)
	
	@property
	def get_cname(self):
		return f'UnseenChatRoomMessages'
	
	@property
	def get_other_user(self):
		if self.user == self.room.user1:
			return self.room.user2
		else:
			return self.room.user1
		
@receiver(post_save, sender=ChatPrivateRoom)
def create_unseen_chatroom_messages_obj(sender, instance, created, **kwargs):
	if created:
		unseen_msgs1 = UnseenChatRoomMessages(room=instance, user=instance.user1)
		unseen_msgs1.save()

		unseen_msgs2 = UnseenChatRoomMessages(room=instance, user=instance.user2)
		unseen_msgs2.save()


@receiver(pre_save, sender=UnseenChatRoomMessages)
def increment_unseen_message_count(sender, instance, **kwargs):
	if instance.id is None:
		pass
	else:
		previous = UnseenChatRoomMessages.objects.get(id=instance.id)
		other_user = ''
		if previous.count < instance.count:
			ct = ContentType.objects.get_for_model(instance)
			if instance.user == instance.room.user1:
				other_user = instance.room.user2
			else:
				other_user = instance.room.user1

			try:
				notification = Notification.objects.get(target=instance.user, content_type=ct, object_id=instance.id)
				notification.verb = instance.most_recent_message
				notification.timestamp = timezone.now()
				notification.save()
			except Notification.DoesNotExist:
				instance.notifications.create(
					target=instance.user,
					from_user=other_user,
					redirect_url=f'{BASE_URL}/chat/?room_id={instance.room.id}/',
					verb=instance.most_recent_message,
					content_type=ct,
				)

@receiver(pre_save, sender=UnseenChatRoomMessages)
def remove_unread_msg_count_notification(sender, instance, **kwargs):
	if instance.id is None:
		pass
	else:
		previous = UnseenChatRoomMessages.objects.get(id=instance.id)
		if previous.count > instance.count:
			content_type = ContentType.objects.get_for_model(instance)
			try:
				notification = Notification.objects.get(target=instance.user, content_type=content_type, object_id=instance.id)
				notification.delete()
			except Notification.DoesNotExist:
				pass
