from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.serializers import serialize
from json import loads, dumps
from .models import ChatRoomMessage, ChatPrivateRoom
from friend.models import FriendList
from django.core.serializers.python import Serializer
from .exceptions import ClientError
from datetime import datetime as dt, timezone as tz
from .utils import set_timestamp
from django.core.paginator import Paginator


DEFAULT_RESULT_SIZE_PER_PAGE = 10
MSG_TYPE_MESSAGE = 0


class ChatConsumer(AsyncJsonWebsocketConsumer):
	async def connect(self):
		"""
		Called when the websocket is handshaking as part of initial connection.
		"""
		print(f'ChatConsumer: connect: {self.scope["user"]}')

		await self.accept()

		self.room_id = None


	async def receive_json(self, content):
		print('ChatConsumer: receive_json')
		command = content.get('command', None)
		try:
			if command == 'join':
				print(f'Joining Room {content['room_id']}')
				await self.join_room(content['room_id'])
			elif command == 'leave':
				await self.leave_room(content['room_id'])
			if command == 'send':
				if len(content['message'].strip()) == 0:
					raise ClientError(422, 'Cannot Send Empty Message')
				await self.send_room(content['room_id'], content['message'])
			elif command == 'get_room_chat_msgs':
				await self.display_progress_bar(True)
				room = await get_room(content['room_id'], self.scope['user'])
				payload = await get_room_chat_msgs(room, content['page_num'])
				if payload is not None:
					payload = loads(payload)
					await self.send_messages_payload(payload['message'], payload['new_page_num'])
				else:
					ClientError(204, 'Something Went Wrong While Loading Chat Room Messages')
				await self.display_progress_bar(False)
			elif command == 'get_user_info':
				await self.display_progress_bar(True)
				room = await get_room(content['room_id'], self.scope['user'])
				payload = get_user_info(room, self.scope['user'])

				if payload is not None:
					payload = loads(payload)
					print(payload)
					await self.send_user_info_payload(payload['user_info'])
				else:
					raise ClientError('ERROR RETRIEVING', 'Something Went Wrong While Retrieveing User Information')
				await self.display_progress_bar(False)
		except ClientError as e:
			await self.display_progress_bar(False)
			await self.handle_client_error(e)


	async def disconnect(self, code, text_data=None, bytes_data=None):
		print(f'\nChatConsumer : disconnect : {self.scope["user"]} : {code}\n')

		try:
			if self.room_id is not None:
				await self.leave(self.room_id)
		except:
			pass		


	async def join_room(self, room_id):
		print(f'ChatConsumer: join_room: {room_id}')

		try:
			room = await get_room(room_id, self.scope['user'])
		except ClientError as e:
			return await self.handle_client_error(e)
		
		self.room_id = room.id

		await self.channel_layer.group_add(
			room.group_name,
			self.channel_name
		)
		
		await self.send_json({
			'join': str(room.id)
		})



	async def leave_room(self, room_id):
		print('ChatConsumer: leave_room')

		room = await get_room(room_id, self.scope['user'])

		await self.channel_layer.group_send(
			room.group_name,
			{
				'type': 'chat.leave',
				'room_id': room_id,
				'profile_image': self.scope['user'].profile_image.url,
				'username': self.scope['user'].username
			}
		)

		self.room_id = None

		await self.channel_layer.group_discard(
			room.group_name,
			self.channel_name
		)

		await self.send_json({
			'leave': str(room.id)
		})



	async def send_room(self, room_id, message):
		print('ChatConsumer: send_room')
		if self.room_id is not None:
			if str(room_id) != str(self.room_id):
				raise ClientError('ROOM ACCESS DENIED', 'Room is unaccessible')
		else:
			raise ClientError('ROOM ACCESS DENIED', 'Room is unaccessible')
			
		room = await get_room(room_id, self.scope['user'])

		await create_room_chat_message(room, self.scope['user'], message)

		await self.channel_layer.group_send(
			room.group_name,
			{
				'type': 'chat.message',
				'profile_image': self.scope['user'].profile_image.url,
				'username': self.scope['user'].username,
				'message': message
			}
		)


	async def chat_message(self, event):
		print('ChatConsumer: chat_message')
		now = dt.now(tz.utc).astimezone()
		ts = set_timestamp(now)
		await self.send_json({
			'msg_type': MSG_TYPE_MESSAGE,
			'username': event['username'],
			'profile_image': event['profile_image'],
			'message': event['message'],
			'timestamp': ts
		})

	async def send_messages_payload(self, messages, new_page_num):
		print('ChatConsumer: send_messages_payload. ')

		await self.send_json({
			'messages_payload': 'messages_payload',
			'messages': messages,
			'new_page_num': new_page_num
		})


	async def send_user_info_payload(self, user_info):
		'''
		Send a payload of user information to the ui
		'''
		print('ChatConsumer: send_user_info_payload. ')
		await self.send_json({
			'user_info': user_info
		})


	async def display_progress_bar(self, is_disp):
		print(f'DISPLAY PROGRESS BAR: {is_disp}')
		await self.send_json({
			'is_disp': is_disp
		})

	async def handle_client_error(self, e):
		errorData = {}
		errorData['error'] = e.code
		if e.message:
			errorData['message'] = e.message
			await self.send_json(errorData)
		return


@database_sync_to_async
def get_room(room_id, user):
	try:
		room = ChatPrivateRoom.objects.get(pk=room_id)
	except ChatPrivateRoom.DoesNotExist as e:
		raise ClientError('INVALID ROOM', f'Room correspoding to the roomID={room_id} does not exists')
	

	if user != room.user1 and user != room.user2:
		raise ClientError('ROOM ACCESS DENIED', 'Entry Denied in the ChatRoom')


	friend_list = FriendList.objects.get(user=user).friends.all()

	if not room.user1 in friend_list:
		if not room.user2 in friend_list:
			raise ClientError('ROOM ACCESS DENIED','You must be a friend to chat')
		
	return room


class LazyChatRoomMessageEncoder(Serializer):
	def get_dump_object(self, obj):
		dump_obj = {}
		dump_obj['msg_type'] = MSG_TYPE_MESSAGE
		dump_obj['msg_id'] = str(obj.id)
		dump_obj['username'] = str(obj.user.username)
		dump_obj['message'] = str(obj.content)
		dump_obj['profile_image'] = str(obj.user.profile_image.url)
		dump_obj['timestamp'] = set_timestamp(obj.timestamp)
		print(f'**{obj}**')
		return dump_obj


def get_user_info(room, user):
	try:
		other_user = room.user1
		if other_user == user:
			other_user = room.user2

		payload = {}

		s = LazyChatAccountEncoder()
		payload['user_info'] = s.serialize([other_user])[0]

		return dumps(payload)
	except ClientError as e:
		raise ClientError("DATA ERROR", "Unable to get that users information")
	return None


class LazyChatAccountEncoder(Serializer):
	def get_dump_object(self, obj):
		dump_object = {}
		dump_object['email']= str(obj.email)
		dump_object['username']= str(obj.username)
		dump_object['profile_image']= str(obj.profile_image.url)
		return dump_object

@database_sync_to_async
def get_room_chat_msgs(room, page_num):
	try:
		query_set = ChatRoomMessage.objects.by_room(room)
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


@database_sync_to_async
def create_room_chat_message(room, user, msg):
	return ChatRoomMessage.objects.create(user=user, room=room, content=msg)







