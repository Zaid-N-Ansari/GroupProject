"""
URL configuration for ProChat project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from . import settings
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib.auth import views as auth_views

from app.views import (
	home_screen_view
)

from account.views import (
	account_search,
	login_view,
	logout_view,
	register_view,
)

urlpatterns = [
    path('', home_screen_view, name='home'),
	
    path('account/', include('account.urls', namespace='account')),

    path('admin/', admin.site.urls),

    path('chat/', include('chat.urls', namespace='chat')),

    path('friend/', include('friend.urls', namespace='friend')),

    path('login/', login_view, name='login'),

    path('logout/', logout_view, name='logout'),

    path('register/', register_view, name='register'),

    path('search/', account_search, name='search'),


    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_reset/password_change_done.html'), 
        name='password_change_done'),

    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='password_reset/password_change.html'), 
        name='password_change'),

    path('password_reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset/password_reset_done.html'),
     name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset/password_reset_complete.html'),
     name='password_reset_complete'),
]

if settings.DEBUG:
	urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
