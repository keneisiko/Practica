from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from rentals.models import Client

# Демо-аккаунты для проверки ролей. Пароль одинаковый, его можно сменить аргументом --password.
DEFAULT_PASSWORD = 'Velo-demo-2026'

DEMO_USERS = [
    ('visitor', User.Role.VISITOR, 'Вера', 'Посетитель'),
    ('client', User.Role.CLIENT, 'Иван', 'Клиентов'),
    ('manager', User.Role.MANAGER, 'Мария', 'Менеджерова'),
    ('admin_demo', User.Role.ADMIN, 'Алексей', 'Админов'),
]


class Command(BaseCommand):
    help = 'Создаёт демо-пользователей всех ролей: visitor, client, manager, admin_demo.'

    def add_arguments(self, parser):
        parser.add_argument('--password', default=DEFAULT_PASSWORD, help='Пароль для всех демо-аккаунтов.')

    @transaction.atomic
    def handle(self, *args, **options):
        password = options['password']
        for username, role, first_name, last_name in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'role': role, 'first_name': first_name, 'last_name': last_name},
            )
            user.role = role
            user.first_name, user.last_name = first_name, last_name
            user.is_staff = role == User.Role.ADMIN  # администратору открыта и Django-админка
            user.set_password(password)
            user.save()
            if role == User.Role.CLIENT:
                Client.objects.update_or_create(
                    user=user,
                    defaults={
                        'last_name': last_name,
                        'first_name': first_name,
                        'phone': '+79990000001',
                        'email': 'client.demo@example.com',
                    },
                )
            action = 'создан' if created else 'обновлён'
            self.stdout.write(f'{username:<11} {user.get_role_display():<14} {action}')
        self.stdout.write(self.style.SUCCESS('Демо-пользователи готовы. Пароль — см. README или --password.'))
