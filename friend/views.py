from django.dispatch import receiver
from django.http import HttpResponse
from json import dumps
from django.shortcuts import redirect, render
from account.models import ChatAccount
from friend.models import FriendList, FriendRequest



def friend_list_view(request, *args, **kwargs):
	context = {}
	user = request.user
	if user.is_authenticated:
		user_id = kwargs.get('user_id')
		if user_id:
			try:
				this_user = ChatAccount.objects.get(pk=user_id)
				context['this_user'] = this_user
			except ChatAccount.DoesNotExist:
				return HttpResponse("User Not Found")
			
			try:
				friend_list = FriendList.objects.get(user=this_user)
				context['this_user'] = this_user
			except FriendList.DoesNotExist:
				return HttpResponse(f'Friend List for {this_user.username} Not Found')
			
			if user != this_user:
				if not user in friend_list.friends.all():
					return HttpResponse("You are not a friend, so you cannot view their Friend List")
				
			friends = []

			user_friend_list = FriendList.objects.get(user=user)
			for friend in friend_list.friends.all():
				friends.append((friend, user_friend_list.is_mutual_friend(friend)))
			
			context['friends'] = friends

	else:
		return HttpResponse('Authentication Required')
	
	return render(request, 'friend/friend_list.html', context)


			

		

def friend_request(request, *args, **kwargs):
	context = {}
	user = request.user
	if user.is_authenticated:
		user_id = kwargs.get('user_id')
		account = ChatAccount.objects.get(pk=user_id)
		if account == user:
			friend_requests = FriendRequest.objects.filter(receiver=account, is_active=True)
			context['friend_requests'] = friend_requests
		else:
			return HttpResponse("Cannot View Another User Friend Request")
	else:
		redirect('login')
	return render(request, 'friend/friend_reqs.html', context)

def send_friend_request(request, *args, **kwargs):
	user = request.user
	payload = {}
	if request.method == "POST" and user.is_authenticated:
		user_id = request.POST.get("receiver_user_id")
		if user_id:
			receiver = ChatAccount.objects.get(pk=user_id)
			try:
				# Get any friend requests (active and not-active)
				friend_requests = FriendRequest.objects.filter(sender=user, receiver=receiver)
				# find if any of them are active (pending)
				try:
					for request in friend_requests:
						if request.is_active:
							raise Exception("You Alrady Sent a Friend Request")
					# If none are active create a new friend request
					friend_request = FriendRequest(sender=user, receiver=receiver)
					friend_request.save()
					payload['response'] = "Friend Request Sent"
				except Exception as e:
					payload['response'] = str(e)
			except FriendRequest.DoesNotExist:
				# There are no friend requests so create one.
				friend_request = FriendRequest(sender=user, receiver=receiver)
				friend_request.save()
				payload['response'] = "Friend Request Sent"

			if payload['response'] == None:
				payload['response'] = "Something went wrong."
		else:
			payload['response'] = "Unable to sent a friend request."
	else:
		payload['response'] = 'Authentication Required'
	return HttpResponse(dumps(payload), content_type='application/json')


def accept_friend_req(request, *args, **kwargs):
	user = request.user
	payload = {}
	if request.method == 'GET' and user.is_authenticated:
		friend_req_id = kwargs.get('friend_req_id')
		if friend_req_id:
			friend_req = FriendRequest.objects.get(pk=friend_req_id)
			if friend_req.receiver == user:
				if friend_req:
					friend_req.accept()
					payload['response'] = 'Friend Request Accepted'
				else:
					payload['response'] = 'Something Went Wrong'
			else:
				payload['response'] = 'This Is Not Your Request To Accept'
		else:
			payload['response'] = 'Unable to Accept Friend Request'
	else:
		payload['response'] = 'Authentication Required'
	
	return HttpResponse(dumps(payload), content_type='application/json')


def remove_friend(request, *args, **kwargs):
	user = request.user
	payload = {}
	if request.method == 'POST' and user.is_authenticated:
		user_id = request.POST.get("receiver_user_id")
		if user_id:
			try:
				removee = ChatAccount.objects.get(pk=user_id)
				friend_list = FriendList.objects.get(user=user)
				friend_list.unfriend(removee)
				payload['response'] = 'Unfriend Successful'
			except Exception as e:
				payload['response'] = str(e)
		else:
			payload['response'] = "Unable to Unfriend"
	else:
		payload['response'] = "Authentication Required"

	return HttpResponse(dumps(payload), content_type='application/json')


def decline_friend_req(request, *args, **kwargs):
	user = request.user
	payload = {}
	if request.method == 'GET' and user.is_authenticated:
		friend_req_id = kwargs.get('friend_req_id')
		if friend_req_id:
			friend_req = FriendRequest.objects.get(pk=friend_req_id)
			if friend_req.receiver == user:
				if friend_req:
					friend_req.decline()
					payload['response'] = 'Friend Request Declined'
				else:
					payload['response'] = 'Something Went Wrong'
			else:
				payload['response'] = 'This Is Not Your Request To Decline'
		else:
			payload['response'] = 'Unable to Decline Friend Request'
	else:
		payload['response'] = 'Authentication Required'
	
	return HttpResponse(dumps(payload), content_type='application/json')


def cancel_friend_req(request, *args, **kwargs):
	user = request.user
	payload = {}
	if request.method == 'POST' and user.is_authenticated:
			user_id = request.POST.get("receiver_user_id")
			if user_id:
				receiver = ChatAccount.objects.get(pk=user_id)
				try:
					friend_requests = FriendRequest.objects.filter(sender=user, receiver=receiver, is_active=True)
				except Exception as e:
					payload['response'] = "No Friend Request Found"
				
				for req in friend_requests:
					req.cancel()
					payload['response'] = "Friend Request Cancelled"
			else:
				payload['response'] = "Unable to Cancel Friend Request"
	else:
		payload['response'] = "Authentication Required"

	return HttpResponse(dumps(payload), content_type='application/json')

