from django.urls import path

from account.views import (
	account_view,
	edit_acc_view,
	crop_image,
)

app_name = 'account'

urlpatterns = [
	path('<user_id>/', account_view, name='view'),
	path('<user_id>/edit/', edit_acc_view, name='edit'),
	path('<user_id>/edit/crop/', crop_image, name='crop'),
]
