from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model

user = get_user_model()

class ChatPublicConsumer(AsyncJsonWebsocketConsumer):

	async def connect(self):
		print(f'\nChatPublicConsumer : connect : {self.scope["user"]}\n')

		await self.accept()

		await self.channel_layer.group_add(
			'chatpublic2',
			self.channel_name
		)


	async def disconnect(self, code, text_data=None, bytes_data=None):
		print(f'\nChatPublicConsumer : disconnect : {self.scope["user"]} : {code}\n')
	

	async def receive_json(self, content, **kwargs):
		command = content.get('command', None)
		msg = content.get('message', None)

		print(f'\nChatPublicConsumer : receive_json : command : {command}\n')
		print(f'ChatPublicConsumer : receive_json : message : {msg}\n')

		await self.send(msg)



	async def send(self, message):
		await self.channel_layer.group_send(
			'chatpublic2',
			{
				'type': 'chat',
				'profile_image': self.scope['user'].profile_image.url,
				'username': self.scope['user'].username,
				'message': message
			}
		)


	async def chat(self, event):
		print(f'\nChatPublicConsumer : chat : {event["username"]}\n')

		await self.send_json({
			'profile_image': event['profile_image'],
			'username': event['username'],
			'message': event['message']
		})


