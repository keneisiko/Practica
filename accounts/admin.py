from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
import accounts.forms as forms

# Register your models here.
# Админка 

@admin.register(User)  # Декоратор для регистрации модели User в админке
class CustomUserAdmin(UserAdmin):
    model = User
    form = forms.CustomUserChangeForm  # Форма для изменения пользователя
    add_form = forms.CustomUserCreationForm  # Форма для создания нового пользователя
    list_display = ['username', 'email', 'role', 'is_staff', 'is_active']  # Поля, которые будут отображаться в списке пользователей
    list_filter = ['role', 'is_staff', 'is_active']  # Фильтры для списка пользователей
    search_fields = ['username', 'email']  # Поля, по которым можно искать пользователей
    ordering = ('username',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'email')}),
        ('Права и роль', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'password1', 'password2'),
        }),
    )