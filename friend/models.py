from django.db import models
from django.shortcuts import redirect
from ProChat.settings import AUTH_USER_MODEL, BASE_URL
from chat.utils import get_private_chat
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from notification.models import Notification
from datetime import datetime as dt, timezone as tz
from django.db.models.signals import post_save
from django.dispatch import receiver


class FriendList(models.Model):
	user = models.OneToOneField(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user')

	friends = models.ManyToManyField(AUTH_USER_MODEL, blank=True, related_name='friends')

	notifications = GenericRelation(Notification)

	def __str__(self):
		return self.user.username
	
	def add_friend(self, acc):
		if not acc in self.friends.all():
			self.friends.add(acc)

			content_type = ContentType.objects.get_for_model(self)
			self.notifications.create(
				target = self.user,
				from_user = acc,
				redirect_url = f'{BASE_URL}/account/{acc.pk}/',
				verb = f'You are a friend of {acc.username}',
				content_type = content_type
			)
			self.save()

			chat = get_private_chat(self.user, acc)
			if not chat.is_active:
				chat.is_active = True
				chat.save()
	

	def remove_friend(self, acc):
		if acc in self.friends.all():
			self.friends.remove(acc)
			chat = get_private_chat(self.user, acc)
			if not chat.is_active:
				chat.is_active = False
				chat.save()


	def unfriend(self, acc):
		self.remove_friend(acc)
		friends_list = FriendList.objects.get(user=acc)
		friends_list.remove_friend(self.user)

		content_type = ContentType.objects.get_for_model(self)
		friends_list.notifications.create(
			target = acc,
			from_user = self.user,
			redirect_url = f'{BASE_URL}/account/{self.user.pk}/',
			verb = f'You are no longer a friend of {self.user.username}',
			content_type = content_type
		)
		
		self.notifications.create(
			target = self.user,
			from_user = acc,
			redirect_url = f'{BASE_URL}/account/{acc.pk}/',
			verb = f'You are no longer a friend of {acc.username}',
			content_type = content_type
		)
		self.save()


	def is_mutual_friend(self, friend):
		if friend in self.friends.all():
			return True
		return False
	
	@property
	def get_cname(self):
		return f'FriendList'
	

class FriendRequest(models.Model):
	sender = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sender')

	receiver = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='receiver')
	
	is_active = models.BooleanField(blank=False, default=True, null=False)

	timestamp = models.DateTimeField(auto_now_add=True)

	notifications = GenericRelation(Notification)

	def __str__(self):
		return self.sender.username
	
	def accept(self):
		receiver_friend_list = FriendList.objects.get(user=self.receiver)

		if receiver_friend_list:
			content_type = ContentType.objects.get_for_model(self)

			receiver_notification = Notification.objects.get(target=self.receiver, content_type=content_type, object_id=self.id)
			receiver_notification.is_active = False
			receiver_notification.redirect_url = f'{BASE_URL}/account/{self.sender.pk}/'
			receiver_notification.verb = f'You accepted {self.sender.username}\'s friend request'
			receiver_notification.timestamp = dt.now(tz.utc).astimezone()
			receiver_notification.save()

			receiver_friend_list.add_friend(self.sender)

			sender_friend_list = FriendList.objects.get(user=self.sender)

			if sender_friend_list:
				self.notifications.create(
					target = self.sender,
					from_user = self.receiver,
					redirect_url = f'{BASE_URL}/account/{self.receiver.pk}/',
					verb = f'{self.receiver.username} accepted your friend request',
					content_type = content_type
				)
				sender_friend_list.add_friend(self.receiver)
				self.is_active = False
				self.save()
			return receiver_notification


	def decline(self):
		self.is_active = False
		self.save()
		content_type = ContentType.objects.get_for_model(self)

		notification = Notification.objects.get(target=self.receiver, content_type=content_type, object_id=self.id)

		notification.is_active = False
		notification.redirect_url = f'{BASE_URL}/account/{self.sender.pk}/'
		notification.verb = f'You declined {self.sender.username}\'s friend request'
		notification.timestamp = dt.now(tz.utc).astimezone()
		notification.save()

		self.notifications.create(
			target = self.sender,
			from_user = self.receiver,
			redirect_url = f'{BASE_URL}/account/{self.receiver.pk}/',
			verb = f'{self.receiver.username} declined your friend request',
			content_type = content_type
		)

		return notification


	def cancel(self):
		self.is_active = False
		self.save()

		content_type = ContentType.objects.get_for_model(self)
		self.notifications.create(
			target = self.sender,
			from_user = self.receiver,
			redirect_url = f'{BASE_URL}/account/{self.receiver.pk}/',
			verb = f'You cancelled the friend the friend request to {self.receiver.username}',
			content_type = content_type
		)

		notification = Notification.objects.get(target=self.receiver, content_type=content_type, object_id=self.id)

		notification.is_active = False
		notification.redirect_url = f'{BASE_URL}/account/{self.sender.pk}/'
		notification.verb = f'{self.sender.username} cancelled the friend request'
		notification.seen = False
		notification.save()
	
	@property
	def get_cname(self):
		return f'FriendRequest'


@receiver(post_save, sender=FriendRequest)
def create_notification(sender, instance, created, **kwargs):
	if created:
		instance.notifications.create(
			target = instance.receiver,
			from_user = instance.sender,
			redirect_url = f'{BASE_URL}/account/{instance.sender.pk}/',
			verb = f'{instance.sender.username} sent you a friend request',
			content_type = instance
		)