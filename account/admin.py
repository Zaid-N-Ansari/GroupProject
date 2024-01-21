from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from account.models import ChatAccount

class ChatAccountAdmin(UserAdmin):
	list_display = ('username','email','date_joined', 'last_login', 'is_admin','is_staff',)
	search_fields = ('email','username',)
	readonly_fields=('username', 'date_joined', 'last_login')

	filter_horizontal = ()
	list_filter = ()
	fieldsets = ()


admin.site.register(ChatAccount, ChatAccountAdmin)