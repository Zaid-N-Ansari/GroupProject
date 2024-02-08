from django.db import models
from ProChat.settings import AUTH_USER_MODEL
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Notification(models.Model):
	target = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)

	from_user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='from_user')
	
	redirect_url = models.URLField(max_length=200, null=True, unique=False, blank=True, help_text='URL when clicked')

	verb = models.CharField(max_length=120, unique=False, blank=True, null=True)

	timestamp = models.DateTimeField(auto_now_add=True)

	seen = models.BooleanField(default=False)

	content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

	object_id = models.PositiveIntegerField()

	content_object = GenericForeignKey()

	def __str__(self):
		return f'{self.verb}'
	
	def get_content_object_type(self):
		return f'{self.content_object.get_cname}'