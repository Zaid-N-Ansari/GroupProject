from json import dumps, loads
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from django.contrib.humanize.templatetags.humanize import naturalday
from datetime import datetime as dt
from django.utils import timezone as tz
import pytz
from .models import ChatPublicRoom, ChatPublicRoomMessage
from channels.db import database_sync_to_async
from django.core.serializers.python import Serializer
from django.core.paginator import Paginator

UserModel = get_user_model()

MSG_TYPE_MESSAGE = 0
DEFAULT_RESULT_SIZE_PER_PAGE = 10
MSG_TYPE_USER_CNT = 1

class ChatPublicConsumer(AsyncJsonWebsocketConsumer):

	async def connect(self):
		print(f'\nChatPublicConsumer : connect : {self.scope['user']}\n')

		await self.accept()

		self.user_id = None


	async def disconnect(self, code, text_data=None, bytes_data=None):
		print(f'\nChatPublicConsumer : disconnect : {self.scope["user"]} : {code}\n')

		try:
			if self.room_id is not None:
				await self.leave(self.room_id)
		except:
			pass
	

	async def receive_json(self, content):
		command = content.get('command', None)

		print(f'\nChatPublicConsumer : receive_json : command : {command}\n')

		try:
			if command == 'send':
				if len(content['message'].strip()) == 0:
					raise ClientError(422, 'Cannot Send Empty Message')
				await self.send(content['room_id'], content['message'])
			elif command == 'join':
				await self.join(content['room_id'])
			elif command == 'leave':
				await self.leave(content['room_id'])
			elif command == 'get_room_chat_msgs':
				await self.display_progess_spinner(True)
				room = await get_room(content['room_id'])
				payload = await get_room_chat_msg(room, content['page_num'])
				if payload != None:
					payload = loads(payload)
					await self.send_msg_payload(payload['message'], payload['new_page_num'])
				else:
					raise ClientError(204, 'Something Went Wrong While Loading Chat Room Messages')
				await self.display_progess_spinner(False)
		except ClientError as e:
			await self.display_progess_spinner(False)
			await self.handle_client_error(e)


	async def send(self, room_id, message):
		print(f'\nChatPublicConsumer : send\n')

		if self.room_id is not None:
			if str(room_id) != str(self.room_id):
				raise ClientError('ROOM ACCESS DENIED', f'You Cannot Access room {room_id}')
			if not is_auth(self.scope['user']):
				raise ClientError('AUTH ERR', 'Authentication Required')
		else:
			raise ClientError('ROOM ACCESS DENIED', f'You Cannot Access Room')
		
		room = await get_room(room_id)

		await create_chat_public_room_message(room, self.scope['user'], message)

		await self.channel_layer.group_send(
			room.group_name,
			{
				'type': 'chat',
				'profile_image': self.scope['user'].profile_image.url,
				'username': self.scope['user'].username,
				'message': message,
			}
		)


	async def chat(self, event):
		print(f'\nChatPublicConsumer : chat : {event}\n')
		utc_time = tz.now().astimezone(pytz.timezone('Asia/Kolkata'))
		ts = set_timestamp(utc_time)
		await self.send_json({
			'msg_type': MSG_TYPE_MESSAGE,
			'profile_image': event['profile_image'],
			'username': event['username'],
			'message': event['message'],
			'timestamp': ts,
		})


	async def join(self, room_id):
		auth = is_auth(self.scope['user'])
		print(f'\nChatPublicConsumer : join\n')
		try:
			room = await get_room(room_id)
		except ClientError as e:
			await self.handle_client_error(e)

		if auth:
			await connect_user(room, self.scope['user'])

		self.room_id = room.id

		await self.channel_layer.group_add(
			room.group_name,
			self.channel_name
		)

		await self.send_json({
			'join': room.id,
			'username': self.scope['user'].username
		})

		num_connected_user = await get_connected_user_count(room)
		await self.channel_layer.group_send(
			room.group_name,
			{
				'type': 'connected.user.count',
				'connected_user_count': num_connected_user
			}
		)


	async def leave(self, room_id):
		print(f'\nChatPublicConsumer : leave\n')
		auth = is_auth(self.scope['user'])
		
		try:
			room = await get_room(room_id)
		except ClientError as e:
			await self.handle_client_error(e)

		if auth:
			await disconnect_user(room, self.scope['user'])

		self.room_id = None

		await self.channel_layer.group_discard(
			room.group_name,
			self.channel_name
		)

		num_connected_user = await get_connected_user_count(room)
		await self.channel_layer.group_send(
			room.group_name,
			{
				'type': 'connected.user.count',
				'connected_user_count': num_connected_user
			}
		)


	async def send_msg_payload(self, message, new_page_num):
		print(f'\nChatPublicConsumer : Send Msg Payload\n')
		await self.send_json({
			'message_payload': 'message_payload',
			'message': message,
			'new_page_num': new_page_num
		})


	async def handle_client_error(self, e):
		errorData = {}
		errorData['error'] = e.code
		if e.message:
			errorData['message'] = e.message
			await self.send_json(errorData)
		return
	

	async def display_progess_spinner(self, is_disp):
		print(f'\nChatPublicConsumer : Display Progess Bar : {str(is_disp)}\n')
		await self.send_json({
			'is_disp': is_disp
		})


	async def connected_user_count(self, event):
		print(f'\nChatPublicConsumer : Number of Users Connected : {event}\n')
		await self.send_json({
			'msg_type': MSG_TYPE_USER_CNT,
			'connected_user_count': event['connected_user_count']
		})


@database_sync_to_async
def get_connected_user_count(room):
	if room.users:
		return len(room.users.all())
	return 0


def is_auth(user):
	if user.is_authenticated:
		return True
	return False


@database_sync_to_async
def create_chat_public_room_message(room, user, msg):
	return ChatPublicRoomMessage.objects.create(user=user, room=room, content=msg)


@database_sync_to_async
def connect_user(room, user):
	return room.connect_user(user)


@database_sync_to_async
def disconnect_user(room, user):
	return room.disconnect_user(user)


@database_sync_to_async
def get_room(room_id):
	try:
		room = ChatPublicRoom.objects.get(pk=room_id)
	except ChatPublicRoom.DoesNotExist:
		raise ClientError('ROOM INVALID', f'Room corresponding to the room_id {room_id} does not exists')
	return room


class ClientError(Exception):
	def __init__(self, code, message):
		super().__init__(code)
		self.code = code
		if message:
			self.message = message


def set_timestamp(timestamp):
	print(timestamp)
	if (naturalday(timestamp) == "today") or (naturalday(timestamp) == "yesterday"):
		str_time = dt.strftime(timestamp, "%I:%M %p")
		str_time = str_time.strip("0")
		ts = f"{naturalday(timestamp)} at {str_time}"
    # other days
	else:
		str_time = dt.strftime(timestamp, "%m/%d/%Y")
		ts = f"{str_time}"

	return str(ts)


@database_sync_to_async
def get_room_chat_msg(room, page_num):
	try:
		query_set = ChatPublicRoomMessage.objects.by_room(room)
		p = Paginator(query_set, DEFAULT_RESULT_SIZE_PER_PAGE)
		payload = {}
		new_page_num = int(page_num)
		if new_page_num <= p.num_pages:
			s = LazyChatRoomMessageEncoder()
			payload['message'] = s.serialize(p.page(page_num).object_list)
			new_page_num += 1
		else:
			payload['message'] = 'None'
		payload['new_page_num'] = new_page_num
		return dumps(payload)
	except Exception as e:
		print(f'\n{str(e)}\n')
		return None


class LazyChatRoomMessageEncoder(Serializer):
	def get_dump_object(self, obj):
		dump_obj = {}
		dump_obj['msg_type'] = MSG_TYPE_MESSAGE
		dump_obj['username'] = str(obj.user.username)
		dump_obj['message'] = str(obj.content)
		dump_obj['profile_image'] = str(obj.user.profile_image.url)
		dump_obj['timestamp'] = set_timestamp(obj.timestamp)
		return dump_obj












