from django.urls import path

from .views import (
	accept_friend_req,
	cancel_friend_req,
	decline_friend_req,
	friend_list_view,
	friend_request,
	remove_friend,
	send_friend_request,
)

app_name = 'friend'

urlpatterns = [
	path('accept/<friend_req_id>', accept_friend_req, name='accept'),
	path('cancel/', cancel_friend_req, name='cancel'),
	path('decline/<friend_req_id>', decline_friend_req, name='decline'),
	path('list/<user_id>', friend_list_view, name='list'),
	path('remove/', remove_friend, name='remove'),
	path('request', send_friend_request, name='request'),
	path('requests/<user_id>', friend_request, name='requests'),
]
