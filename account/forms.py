from django import forms
from django.contrib.auth.forms import UserCreationForm
from account.models import ChatAccount
from django.contrib.auth import authenticate


class RegistrationForm(UserCreationForm):
	email = forms.EmailField(max_length=254, help_text='Required. Add a valid email address.')

	class Meta:
		model = ChatAccount
		fields = ('username', 'email', 'password1', 'password2',)

	def clean_email(self):
		email = self.cleaned_data['email'].lower()
		try:
			acc = ChatAccount.objects.exclude(pk=self.instance.pk).get(email=email)
		except ChatAccount.DoesNotExist:
			return email
		raise forms.ValidationError(f'{email} Is Already Used')

	def clean_username(self):
		username = self.cleaned_data['username']
		try:
			acc = ChatAccount.objects.exclude(pk=self.instance.pk).get(username=username)
		except ChatAccount.DoesNotExist:
			return username
		raise forms.ValidationError(f'{username} Is Already Used')
	
class AccountAuthenticateForm(forms.ModelForm):
	password = forms.CharField(label='Password', widget=forms.PasswordInput)

	class Meta:
		model = ChatAccount
		fields = ('username', 'password')

	def clean(self):
		if self.is_valid():
			username = self.cleaned_data['username']
			password = self.cleaned_data['password']
			if not authenticate(username=username, password=password):
				raise forms.ValidationError('InValid Login')

class AccountUpdateForm(forms.ModelForm):
	class Meta:
		model = ChatAccount
		fields = ('email', 'profile_image', 'hide_email')

	def clean_email(self):
		email = self.cleaned_data['email'].lower()
		try:
			acc = ChatAccount.objects.exclude(pk=self.instance.pk).get(email=email)
		except ChatAccount.DoesNotExist:
			return email
		raise forms.ValidationError(f'{email} Is Already Used')

	def save(self, commit=True):
		acc = super(AccountUpdateForm, self).save(commit=False)
		acc.email = self.cleaned_data['email']
		acc.hide_email = self.cleaned_data['hide_email']
		if commit:
			acc.save()

		return acc



