from django.urls import path
from .views import (
	private_chat_room_view,
	create_private_chat
)


app_name = 'chat'


urlpatterns = [
	path('', private_chat_room_view, name='private-chat-room'),
	path('private-chat/', create_private_chat, name='create-private-chat'),
]