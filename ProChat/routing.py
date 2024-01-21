from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path
from django.core.asgi import get_asgi_application
from chatpublic.consumers import ChatPublicConsumer

application = ProtocolTypeRouter({
	'http': get_asgi_application(),
	'websocket': AllowedHostsOriginValidator(
		AuthMiddlewareStack(
			URLRouter([
				path('chatpublic/<room_id>/', ChatPublicConsumer.as_asgi()),
			])
		)
	),
})
