from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User
from django import forms

class CustomUserCreationForm(UserCreationForm):  # Это форма для создания нового пользователя, которая наследуется от стандартной формы UserCreationForm в админке
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'role')

class CustomUserChangeForm(UserChangeForm):  # А это редактирование пользователя
    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"

class RegisterForm(UserCreationForm):  # Форма регистрации для обычных пользователей
    last_name = forms.CharField(max_length=50, label='Фамилия')
    first_name = forms.CharField(max_length=50, label='Имя')
    phone = forms.CharField(max_length=50, label='Телефон')
    email = forms.EmailField(required=False, label='Email')
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email',)