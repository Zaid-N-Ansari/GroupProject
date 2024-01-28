from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path
from django.core.asgi import get_asgi_application
from chatpublic.consumers import ChatPublicConsumer
from chat.consumers import ChatConsumer

application = ProtocolTypeRouter({
	'http': get_asgi_application(),
	'websocket': AllowedHostsOriginValidator(
		AuthMiddlewareStack(
			URLRouter([
				path('chat/<room_id>/', ChatConsumer.as_asgi()),
				path('chatpublic/<room_id>/', ChatPublicConsumer.as_asgi()),
			])
		)
	),
})
