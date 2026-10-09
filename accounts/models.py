from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):  # По тупому это таблица джанго преобразует этот class в таблицу базы данных, а AbstractUser - это базовая модель пользователя, которая уже содержит стандартные поля, такие как username, email, password и т.д.
    class Role(models.TextChoices):  
        VISITOR = 'visitor', 'Посетитель'
        CLIENT = 'client', 'Клиент'
        MANAGER = 'manager', 'Менеджер'
        ADMIN = 'admin', 'Администратор'
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT,
        verbose_name='Роль',
    )
    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'