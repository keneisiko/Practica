from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Пользователь системы. Роль определяет, какие функции ему доступны."""

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

    # Проверки ролей собраны здесь, чтобы во вьюхах и шаблонах не сравнивать строки.
    # Суперпользователь (createsuperuser) считается администратором независимо от поля role.

    @property
    def is_admin_role(self):
        return self.is_superuser or self.role == self.Role.ADMIN

    @property
    def is_manager_role(self):
        """Менеджер или администратор: администратору доступно всё, что менеджеру."""
        return self.is_admin_role or self.role == self.Role.MANAGER

    @property
    def is_client_role(self):
        return not self.is_manager_role and self.role == self.Role.CLIENT

    @property
    def can_rent(self):
        """Оформлять прокат могут клиент (на себя), менеджер и администратор (на клиента)."""
        return self.is_manager_role or self.is_client_role

    @property
    def can_search_catalog(self):
        """Поиск, фильтры и сортировка — для всех авторизованных, кроме посетителя."""
        return self.can_rent

    @property
    def role_label(self):
        if self.is_superuser and self.role != self.Role.ADMIN:
            return self.Role.ADMIN.label
        return self.get_role_display()
