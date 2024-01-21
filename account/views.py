from math import e
from msilib.schema import File
from django.dispatch import receiver
from django.shortcuts import render, redirect
from django.http import HttpResponse
from os.path import exists, join
from os import mkdir, remove
from base64 import b64decode
from account.models import ChatAccount
from json import dumps
from django.core.files import File
from cv2 import imread, imwrite
import requests
from friend.models import FriendList, FriendRequest
from friend.friend_req_status import FriendReqStatus
from friend.utils import get_friend_req

from django.contrib.auth import (
	login,
	logout,
	authenticate,
)

from account.forms import (
	RegistrationForm,
	AccountAuthenticateForm,
	AccountUpdateForm,
)

from ProChat.settings import (
	TEMP,
	BASE_URL,
	IMAGE_MAX_UPLOAD_SIZE
)

from django.core.files.storage import (
	default_storage,
	FileSystemStorage
)


TMP_PROFILE_IMAGE_NAME = 'tmp_profile_image.png'

def register_view(request, *args, **kwargs):
	user = request.user
	if user.is_authenticated: 
		return HttpResponse("You are already authenticated as " + str(user.email))

	context = {}
	if request.POST:
		form = RegistrationForm(request.POST)
		if form.is_valid():
			form.save()
			username = form.cleaned_data.get('username')
			raw_password = form.cleaned_data.get('password1')
			account = authenticate(request, username=username, password=raw_password)
			login(request, account)
			return redirect('home')
		else:
			context['registration_form'] = form

	else:
		form = RegistrationForm()
		context['registration_form'] = form
	return render(request, 'account/register.html', context)

def logout_view(request):
	logout(request)
	return redirect('home')


def login_view(request, *args, **kwargs):
	context = {}
	user = request.user
	if user.is_authenticated:
		return redirect('home')

	if request.POST:
		form = AccountAuthenticateForm(request.POST)
		if form.is_valid():
			username = request.POST['username']
			password = request.POST['password']
			user = authenticate(request, username=username, password=password)
			if user:
				login(request, user)
				dest = request.GET.get('next', None)
				if dest:
					return redirect(dest)
				return redirect('home')
		else:
			context['login_form'] = form
	return render(request, 'account/login.html', context)


def account_view(request, *args, **kwargs):
	"""
	- Logic here is kind of tricky
		is_self
		is_friend
			-1: NO_REQUEST_SENT
			0: THEM_SENT_TO_YOU
			1: YOU_SENT_TO_THEM
	"""
	context = {}
	user_id = kwargs.get("user_id")
	try:
		account = ChatAccount.objects.get(pk=user_id)
	except:
		return HttpResponse("Something went wrong.")
	if account:
		context['username'] = account.username
		context['email'] = account.email
		context['profile_image'] = account.profile_image.url
		context['hide_email'] = account.hide_email

		try:
			friend_list = FriendList.objects.get(user=account)
		except FriendList.DoesNotExist:
			friend_list = FriendList(user=account)
			friend_list.save()
		friends = friend_list.friends.all()
		context['friends'] = friends
	
		# Define template variables
		is_self = True
		is_friend = False
		request_sent = FriendReqStatus.NO_REQ_SENT.value # range: ENUM -> friend/friend_request_status.FriendRequestStatus
		friend_requests = None
		user = request.user
		if user.is_authenticated and user != account:
			is_self = False
			if friends.filter(pk=user.username):
				is_friend = True
			else:
				is_friend = False
				# CASE1: Request has been sent from THEM to YOU: FriendRequestStatus.THEM_SENT_TO_YOU
				if get_friend_req(sender=account, receiver=user) != False:
					request_sent = FriendReqStatus.SENT_TO_YOU.value
					context['pending_friend_request_id'] = get_friend_req(sender=account, receiver=user).id
				# CASE2: Request has been sent from YOU to THEM: FriendRequestStatus.YOU_SENT_TO_THEM
				elif get_friend_req(sender=user, receiver=account) != False:
					request_sent = FriendReqStatus.YOU_SENT_THEM.value
				# CASE3: No request sent from YOU or THEM: FriendRequestStatus.NO_REQUEST_SENT
				else:
					request_sent = FriendReqStatus.NO_REQ_SENT.value
		
		elif not user.is_authenticated:
			is_self = False
		else:
			try:
				friend_requests = FriendRequest.objects.filter(receiver=user, is_active=True)
			except:
				pass
			
		# Set the template variables to the values
		context['is_self'] = is_self
		context['is_friend'] = is_friend
		context['request_sent'] = request_sent
		context['friend_requests'] = friend_requests
		context['BASE_URL'] = BASE_URL
		return render(request, "account/account.html", context)


def account_search(request, *args, **kwargs):
	context = {}
	if request.method == "GET":
		search_query = request.GET.get("q")

		if len(search_query) > 0:
			search_results = ChatAccount.objects.filter(email__icontains=search_query).filter(username__icontains=search_query).distinct()

			user = request.user
			accounts = []

			if user.is_authenticated:
				auth_user_friend_list = FriendList.objects.get(user=user)
				for account in search_results:
					accounts.append((account, auth_user_friend_list.is_mutual_friend(account)))
				context['accounts'] = accounts

			else:
				for account in search_results:
					accounts.append((account, False))
				context['accounts'] = accounts
				
	return render(request, "account/search_user.html", context)

def edit_acc_view(request, *args, **kwargs):
	if not request.user.is_authenticated:
		return redirect('login')
	user_id = kwargs.get('user_id')
	try:
		acc = ChatAccount.objects.get(pk=user_id)
	except ChatAccount.DoesNotExist:
		return HttpResponse('Something Went Wrong')
	
	if acc.pk != request.user.pk:
		return HttpResponse('Edit Unauthorized')

	context = {}

	if request.POST:
		form = AccountUpdateForm(request.POST, request.FILES, instance=request.user)
		if form.is_valid():
			form.save()
			return redirect('account:view', user_id=acc.pk)
		else:
			form = AccountUpdateForm(
				request.POST,
				instance=request.user,
				initial={
				'id': acc.pk,
				'email': acc.email,
				'username': acc.username,
				'profile_image': acc.profile_image,
				'hide_email': acc.hide_email,
				}
			)

			context['form'] = form
	else:
		form = AccountUpdateForm(
			initial={
				'id': acc.pk,
				'email': acc.email,
				'username': acc.username,
				'profile_image': acc.profile_image,
				'hide_email': acc.hide_email,
				}
			)

		context['form'] = form

	context['IMAGE_MAX_UPLOAD_SIZE'] = IMAGE_MAX_UPLOAD_SIZE

	return render(request, 'account/edit_account.html', context)


def save_tmp_profile_img(imgStr, user):
	INCORRECT_PADDING_EXCP = 'Incorrect padding'
	try:
		if not exists(TEMP):
			mkdir(TEMP)
		if not exists(f'{TEMP}/{user.pk}'):
			mkdir(f'{TEMP}/{user.pk}')
	
		url = join(f'{TEMP}/{user.pk}', TMP_PROFILE_IMAGE_NAME)
		storage = FileSystemStorage(location=url)
		img = b64decode(imgStr)
		with storage.open('', 'wb+') as dest:
			dest.write(img)
			dest.close()

		return url

	except Exception as e:
		if str(e) == INCORRECT_PADDING_EXCP:
			imgStr += '=' * ((4 - len(imgStr) % 4) % 4)
			return save_tmp_profile_img(imgStr, user)


def crop_image(request, *args, **kwargs):
	payload = {}
	user = request.user
	if request.POST and user.is_authenticated:
		try:
			imgStr = request.POST.get('image')
			url = save_tmp_profile_img(imgStr, user)
			img = imread(url)
			cropX = int(float(str(request.POST.get('cropX'))))
			cropY = int(float(str(request.POST.get('cropY'))))
			cropW = int(float(str(request.POST.get('cropW'))))
			cropH = int(float(str(request.POST.get('cropH'))))

			if cropX < 0:
				cropX = 0
			if cropY < 0:
				cropY = 0

			crop_img = img[cropY:cropY+cropH, cropX:cropX+cropW]

			imwrite(url, crop_img)

			user.profile_image.delete()

			user.profile_image.save('profile_image.png', File(open(url, 'rb')))

			user.save()

			payload['result'] = 'success'
			payload['cropped_profile_image'] = user.profile_image.url

			remove(url)


		except Exception as e:
			payload['result'] = 'error'
			payload['exception'] = str(e)

	return HttpResponse(dumps(payload), content_type='application/json')