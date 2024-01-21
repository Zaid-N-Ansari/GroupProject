from django.db import models

from ProChat.settings import (
	AUTH_USER_MODEL,
)

from django.utils import timezone


class FriendList(models.Model):
	user = models.OneToOneField(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user')

	friends = models.ManyToManyField(AUTH_USER_MODEL, blank=True, related_name='friends')
	
	def __str__(self):
		return self.user.username
	
	def add_friend(self, acc):
		if not acc in self.friends.all():
			self.friends.add(acc)
	
	def remove_friend(self, acc):
		if acc in self.friends.all():
			self.friends.remove(acc)

	def unfriend(self, acc):
		self.remove_friend(acc)

		friends_list = FriendList.objects.get(user=acc)

		friends_list.remove_friend(self.user)

	def is_mutual_friend(self, friend):
		if friend in self.friends.all():
			return True
	
		return False
	

class FriendRequest(models.Model):
	sender = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sender')

	receiver = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='receiver')
	
	is_active = models.BooleanField(blank=True, default=True, null=False)

	timestamp = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.sender.username
	
	def accept(self):
		receiver_friend_list = FriendList.objects.get(user=self.receiver)

		if receiver_friend_list:
			receiver_friend_list.add_friend(self.sender)

			sender_friend_list = FriendList.objects.get(user=self.sender)

			if sender_friend_list:
				sender_friend_list.add_friend(self.receiver)
				self.is_active = False
				self.save()


	def decline(self):
		self.is_active = False
		self.save()


	def cancel(self):
		self.is_active = False
		self.save()
