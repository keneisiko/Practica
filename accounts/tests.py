from django.test import TestCase
from django.urls import reverse

from rentals.models import Client

from .models import User


class AuthTest(TestCase):
    def test_login_by_username(self):
        User.objects.create_user('manager', password='pass-12345', role=User.Role.MANAGER)
        response = self.client.post(reverse('accounts:login'), {'username': 'manager', 'password': 'pass-12345'})
        self.assertRedirects(response, reverse('catalog:bike_list'), fetch_redirect_response=False)

    def test_wrong_password_shows_message(self):
        response = self.client.post(reverse('accounts:login'), {'username': 'nobody', 'password': 'x'})
        self.assertContains(response, 'Неверный логин или пароль')

    def test_registration_creates_client(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newbie', 'last_name': 'Новиков', 'first_name': 'Николай',
            'phone': '+7 (900) 111-22-33', 'email': 'n@example.com',
            'password1': 'Strong-pass-2026', 'password2': 'Strong-pass-2026',
        })
        self.assertRedirects(response, reverse('catalog:bike_list'))
        user = User.objects.get(username='newbie')
        self.assertEqual(user.role, User.Role.CLIENT)
        self.assertEqual(user.client_profile.phone, '+79001112233')

    def test_registration_rejects_duplicate_phone(self):
        Client.objects.create(last_name='Иванов', first_name='Иван', phone='+79001112233')
        response = self.client.post(reverse('accounts:register'), {
            'username': 'dup', 'last_name': 'Д', 'first_name': 'Д', 'phone': '+79001112233',
            'password1': 'Strong-pass-2026', 'password2': 'Strong-pass-2026',
        })
        self.assertContains(response, 'Клиент с таким телефоном уже зарегистрирован.')
        self.assertFalse(User.objects.filter(username='dup').exists())


class RolePropertiesTest(TestCase):
    def test_roles(self):
        cases = {
            User.Role.VISITOR: (False, False, False),
            User.Role.CLIENT: (True, False, False),
            User.Role.MANAGER: (True, True, False),
            User.Role.ADMIN: (True, True, True),
        }
        for role, (can_rent, is_manager, is_admin) in cases.items():
            with self.subTest(role=role):
                user = User(username=role, role=role)
                self.assertEqual((user.can_rent, user.is_manager_role, user.is_admin_role), (can_rent, is_manager, is_admin))

    def test_superuser_is_admin(self):
        user = User(username='root', role=User.Role.CLIENT, is_superuser=True)
        self.assertTrue(user.is_admin_role)
        self.assertEqual(user.role_label, 'Администратор')
