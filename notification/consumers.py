from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.paginator import Paginator
from channels.db import database_sync_to_async
from django.contrib.contenttypes.models import ContentType
from json import dumps, loads
from friend.models import FriendRequest, FriendList
import notification
from notification.models import Notification
from notification.utils import LazyNotificationEncoder
from chat.exceptions import ClientError
from datetime import datetime as dt
from chat.models import UnseenChatRoomMessages


DEFAULT_NOTIFICATION_PAGE_SIZE = 10
GENERAL_MSG_TYPE_NOTIFICATIONS_PAYLOAD = 0
GENERAL_MSG_TYPE_PAGINATION_EXHAUSTED = 1
GENERAL_MSG_TYPE_NOTIFICATIONS_REFRESH_PAYLOAD = 2
GENERAL_MSG_TYPE_GET_NEW_NOTIFICATIONS = 3
GENERAL_MSG_TYPE_GET_UNSEEN_NOTIFICATIONS_COUNT = 4
GENERAL_MSG_TYPE_UPDATED_NOTIFICATION = 5

CHAT_MSG_TYPE_NOTIFICATIONS_PAYLOAD = 10
CHAT_MSG_TYPE_PAGINATION_EXHAUST = 11
CHAT_MSG_TYPE_GET_NEW_NOTIFICATIONS = 13
CHAT_MSG_TYPE_GET_UNSEEN_NOTIFICATIONS_COUNT = 14



class NotificationConsumer(AsyncJsonWebsocketConsumer):
	async def connect(self):
		print("NotificationConsumer: connect: " + str(self.scope["user"]) )
		await self.accept()


	async def disconnect(self, code):
		print("NotificationConsumer: disconnect")
		self.disconnect(code)


	async def receive_json(self, content):
		command = content.get("command", None)
		print("NotificationConsumer: receive_json. Command: " + command)
		try:
			if command == "get_general_notifications":
				payload = await get_general_notifications(self.scope["user"], content["page_number"])
				if payload is None:
					await self.general_pagination_exhausted()
				else:
					payload = loads(payload)
					await self.send_general_notifications_payload(payload['notifications'], payload['new_page_number'])
			elif command == "accept_friend_req":
				notification_id = content['notification_id']
				payload = await accept_friend_request(self.scope['user'], notification_id)
				if payload == None:
					raise ClientError("Something went wrong. Try refreshing the browser.")
				else:
					payload = loads(payload)
					await self.send_updated_friend_request_notification(payload['notification'])
			elif command == "decline_friend_req":
				notification_id = content['notification_id']
				payload = await decline_friend_request(self.scope['user'], notification_id)
				if payload is None:
					raise ClientError(204, "Something went wrong. Try refreshing the browser.")
				else:
					payload = loads(payload)
					await self.send_updated_friend_request_notification(payload['notification'])
			elif command == 'refresh_general_notifications':
				payload = await refresh_general_notifications(self.scope['user'], content['oldest_timestamp'], content['newest_timestamp'])
				if payload is None:
					raise ClientError(204, "Something went wrong. Try refreshing the browser.")
				else:
					payload = loads(payload)
					await self.send_general_refreshed_notifications_payload(payload['notifications'])
			elif command == 'get_new_general_notifications':
				payload = await get_new_general_notifications(self.scope['user'], content['newest_timestamp'])
				if payload is not None:
					payload = loads(payload)
					await self.send_new_general_notifications_payload(payload['notifications'])
			elif command == 'get_unseen_general_notifications_count':
				payload = await get_unseen_general_notifications_count(self.scope['user'])
				if payload is not None:
					payload = loads(payload)
					await self.send_unseen_general_notifications_count(payload['count'])
			elif command == 'mark_notifications_seen':
				await mark_notifications_seen(self.scope['user'])
			elif command == 'get_chat_notifications':
				payload = await get_chat_notifications(self.scope['user'], content.get('page_number', None))
				if payload is None:
					await self.chat_pagination_exhaust()
				else:
					payload = loads(payload)
					await self.send_chat_notifications_payload(payload['notifications'], payload['new_page_number']) 
			elif command == 'get_new_chat_notifications':
				payload = await get_new_chat_notifications(self.scope['user'], content['newest_timestamp'])
				if payload is not None:
					payload = loads(payload)
					await self.send_new_chat_notifications_payload(payload['notifications'])
			elif command == 'get_unseen_chat_notifications_count':
				payload = await get_unseen_chat_notifications_count(self.scope['user'])
				if payload is not None:
					payload = loads(payload)
					await self.send_unseen_chat_notifications_count(payload['count'])
		except ClientError as e:
			print("EXCEPTION: receive_json: " + str(e))

	async def display_progress_bar(self, shouldDisplay):
		print("NotificationConsumer: display_progress_bar: " + str(shouldDisplay)) 
		await self.send_json(
			{
				"progress_bar": shouldDisplay,
			},
		)

	async def send_general_notifications_payload(self, notifications, new_page_number):
		"""
		Called by receive_json when ready to send a json array of the notifications
		"""
		print("NotificationConsumer: send_general_notifications_payload")
		await self.send_json(
			{
				"general_msg_type": GENERAL_MSG_TYPE_NOTIFICATIONS_PAYLOAD,
				"notifications": notifications,
				"new_page_number": new_page_number,
			},
		)

	async def send_updated_friend_request_notification(self, notification):
		"""
		After a friend request is accepted or declined, send the updated notification to template
		payload contains 'notification' and 'response':
		1. payload['notification']
		2. payload['response']
		"""
		await self.send_json(
			{
				"general_msg_type": GENERAL_MSG_TYPE_UPDATED_NOTIFICATION,
				"notification": notification,
			},
		)

	async def general_pagination_exhausted(self):
		"""
		Called by receive_json when pagination is exhausted for general notifications
		"""
		print("General Pagination DONE... No more notifications.")
		await self.send_json(
			{
				"general_msg_type": GENERAL_MSG_TYPE_PAGINATION_EXHAUSTED,
			},
		)

	async def send_general_refreshed_notifications_payload(self, notifications):
		await self.send_json({
			"general_msg_type": GENERAL_MSG_TYPE_NOTIFICATIONS_REFRESH_PAYLOAD,
			"notifications": notifications
		})

	async def send_new_general_notifications_payload(self, notifications):
		await self.send_json({
			'general_msg_type': GENERAL_MSG_TYPE_GET_NEW_NOTIFICATIONS,
			'notifications': notifications
		})

	async def send_unseen_general_notifications_count(self, count):
		await self.send_json({
			'general_msg_type': GENERAL_MSG_TYPE_GET_UNSEEN_NOTIFICATIONS_COUNT,
			'count': count
		})

	async def send_chat_notifications_payload(self, notifications, new_page_num):
		await self.send_json({
			'chat_msg_type': CHAT_MSG_TYPE_NOTIFICATIONS_PAYLOAD,
			'notifications': notifications,
			'new_page_number': new_page_num
		})

	async def send_new_chat_notifications_payload(self, notifications):
		await self.send_json({
			'chat_msg_type': CHAT_MSG_TYPE_GET_NEW_NOTIFICATIONS,
			'notifications': notifications
		})

	async def chat_pagination_exhaust(self):
		await self.send_json({
			'chat_msg_type': CHAT_MSG_TYPE_PAGINATION_EXHAUST
		})

	async def send_unseen_chat_notifications_count(self, count):
		await self.send_json({
			'chat_msg_type': CHAT_MSG_TYPE_GET_UNSEEN_NOTIFICATIONS_COUNT,
			'count': count
		})





@database_sync_to_async
def get_general_notifications(user, page_number):
	"""
	Get General Notifications with Pagination (next page of results).
	This is for appending to the bottom of the notifications list.
	General Notifications are:
	1. FriendRequest
	2. FriendList
	"""
	if user.is_authenticated:
		friend_request_ct = ContentType.objects.get_for_model(FriendRequest)
		friend_list_ct = ContentType.objects.get_for_model(FriendList)
		notifications = Notification.objects.filter(target=user, content_type__in=[friend_request_ct, friend_list_ct]).order_by('-timestamp')
		p = Paginator(notifications, DEFAULT_NOTIFICATION_PAGE_SIZE)

		payload = {}
		if len(notifications) > 0:
			if int(page_number) <= p.num_pages:
				s = LazyNotificationEncoder()
				serialized_notifications = s.serialize(p.page(page_number).object_list)
				payload['notifications'] = serialized_notifications
				new_page_number = int(page_number) + 1
				payload['new_page_number'] = new_page_number
			if payload.keys().__len__() == 0:
				return None
		else:
			return None
	else:
		raise ClientError("Authentication Required")

	return dumps(payload)


@database_sync_to_async
def accept_friend_request(user, notification_id):
    """
    Accept a friend request
    """
    payload = {}
    if user.is_authenticated:
        try:
            notification = Notification.objects.get(pk=notification_id)
            friend_request = notification.content_object
            # confirm this is the correct user
            if friend_request.receiver == user:
                # accept the request and get the updated notification
                updated_notification = friend_request.accept()

                # return the notification associated with this FriendRequest
                s = LazyNotificationEncoder()
                payload['notification'] = s.serialize([updated_notification])[0]
                return dumps(payload)
        except Notification.DoesNotExist:
            raise ClientError("An error occurred with that notification. Try refreshing the browser.")
    return None


@database_sync_to_async
def decline_friend_request(user, notification_id):
	"""
	Decline a friend request
	"""
	payload = {}
	if user.is_authenticated:
		try:
			notification = Notification.objects.get(pk=notification_id)
			friend_request = notification.content_object
			# confirm this is the correct user
			if friend_request.receiver == user:
				# accept the request and get the updated notification
				updated_notification = friend_request.decline()

				# return the notification associated with this FriendRequest
				s = LazyNotificationEncoder()
				payload['notification'] = s.serialize([updated_notification])[0]
				return dumps(payload)
		except Notification.DoesNotExist:
			raise ClientError("An error occurred with that notification. Try refreshing the browser.")
	return None


@database_sync_to_async
def refresh_general_notifications(user, oldest_timestamp:str, newest_timestamp:str):
	payload = {}
	if user.is_authenticated:
		if newest_timestamp == '':
			newest_timestamp = oldest_timestamp
		oldest_ts = oldest_timestamp[0:oldest_timestamp.find("+")]
		oldest_ts = dt.strptime(oldest_ts, '%Y-%m-%d %H:%M:%S.%f')
		newest_ts = newest_timestamp[0:newest_timestamp.find("+")]
		newest_ts = dt.strptime(newest_ts, '%Y-%m-%d %H:%M:%S.%f')
		friend_request_ct = ContentType.objects.get_for_model(FriendRequest)
		friend_list_ct = ContentType.objects.get_for_model(FriendList)
		notifications = Notification.objects.filter(target=user, content_type__in=[friend_request_ct, friend_list_ct], timestamp__gte=oldest_ts, timestamp__lte=newest_ts).order_by('-timestamp')

		s = LazyNotificationEncoder()
		payload['notifications'] = s.serialize(notifications)
	else:
		raise ClientError("Authentication Needed")

	return dumps(payload) 



@database_sync_to_async
def get_new_general_notifications(user, newestTS:str):
	payload = {}
	if user.is_authenticated:
		timestamp = newestTS[0:newestTS.find('+')]
		timestamp = dt.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
		friend_request_ct = ContentType.objects.get_for_model(FriendRequest)
		friend_list_ct = ContentType.objects.get_for_model(FriendList)
		notifications = Notification.objects.filter(target=user, content_type__in=[friend_request_ct, friend_list_ct], timestamp__gt=newestTS, seen=False).order_by('-timestamp')
		s = LazyNotificationEncoder()
		payload['notifications'] = s.serialize(notifications)
		return dumps(payload)
	else:
		raise ClientError(204, 'Authentication Required')
	return None


@database_sync_to_async
def get_unseen_general_notifications_count(user):
	payload = {}
	if user.is_authenticated:
		friend_request_ct = ContentType.objects.get_for_model(FriendRequest)
		friend_list_ct = ContentType.objects.get_for_model(FriendList)
		notifications = Notification.objects.filter(target=user, content_type__in=[friend_request_ct, friend_list_ct], seen=False)
		unseen_count = 0
		if notifications:
			for notification in notifications.all():
				if not notification.seen:
					unseen_count += 1
		payload['count'] = unseen_count
	else:
		raise ClientError(204, 'Authentication Required')
	return dumps(payload)


@database_sync_to_async
def mark_notifications_seen(user):
	if user.is_authenticated:
		notifications = Notification.objects.filter(target=user)
		if notifications:
			for notification in notifications.all():
				notification.seen = True
				notification.save()
	return


@database_sync_to_async
def get_chat_notifications(user, page_number):
	if user.is_authenticated:
		ct = ContentType.objects.get_for_model(UnseenChatRoomMessages)
		notifications = Notification.objects.filter(target=user, content_type=ct).order_by('-timestamp')
		p = Paginator(notifications, DEFAULT_NOTIFICATION_PAGE_SIZE)

		payload = {}
		if len(notifications) > 0:
			if int(page_number) <= p.num_pages:
				s = LazyNotificationEncoder()
				serialized_notifications = s.serialize(p.page(page_number).object_list)
				payload['notifications'] = serialized_notifications
				new_page_number = int(page_number) + 1
				payload['new_page_number'] = new_page_number
				return dumps(payload)
		else:
			return None
	else:
		raise ClientError("Authentication Required")
	return None


@database_sync_to_async
def get_new_chat_notifications(user, newestTS):
	payload = {}
	if user.is_authenticated:
		timestamp = newestTS[0:newestTS.find('+')]
		timestamp = dt.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
		chatmessage_ct = ContentType.objects.get_for_model(UnseenChatRoomMessages)
		notifications = Notification.objects.filter(target=user, content_type=chatmessage_ct, timestamp__gt=timestamp, seen=False).order_by('-timestamp')
		s = LazyNotificationEncoder()
		payload['notifications'] = s.serialize(notifications)
		return dumps(payload) 
	else:
		raise ClientError("AUTH_ERROR", "Authentication Required")
	return None


@database_sync_to_async
def get_unseen_chat_notifications_count(user):
    payload = {}
    if user.is_authenticated:
        chatmessage_ct = ContentType.objects.get_for_model(UnseenChatRoomMessages)
        notifications = Notification.objects.filter(target=user, content_type__in=[chatmessage_ct])
        unread_count = 0
        if notifications:
            unread_count = len(notifications.all())
        payload['count'] = unread_count
        return dumps(payload)
    else:
        raise ClientError("AUTH_ERROR", "User must be authenticated to get notifications.")
    return None