import re

from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from rentals.forms import PHONE_RE
from rentals.models import Client

from .models import User


class CustomUserCreationForm(UserCreationForm):  # создание пользователя в админке
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'role')


class CustomUserChangeForm(UserChangeForm):  # редактирование пользователя в админке
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'


class RegisterForm(UserCreationForm):
    """Регистрация клиента: пользователь + профиль клиента."""

    last_name = forms.CharField(max_length=50, label='Фамилия')
    first_name = forms.CharField(max_length=50, label='Имя')
    phone = forms.CharField(
        max_length=20,
        label='Телефон',
        widget=forms.TextInput(attrs={'placeholder': '+79000000000', 'type': 'tel'}),
    )
    email = forms.EmailField(required=False, label='Email')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username',)

    def clean_phone(self):
        phone = re.sub(r'[\s()-]', '', self.cleaned_data['phone'])
        if not PHONE_RE.match(phone):
            raise forms.ValidationError('Телефон: от 10 до 15 цифр, можно с «+» в начале.')
        if Client.objects.filter(phone=phone).exists():
            raise forms.ValidationError('Клиент с таким телефоном уже зарегистрирован.')
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email') or None
        if email and Client.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Клиент с таким email уже зарегистрирован.')
        return email
