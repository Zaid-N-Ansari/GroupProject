from .models import FriendRequest


def get_friend_req(sender, receiver):
	try:
		return FriendRequest.objects.get(sender=sender, receiver=receiver, is_active=True)
	except FriendRequest.DoesNotExist:
		return False



