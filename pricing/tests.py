"""Тесты интеграции модуля расчёта `rental_cost` с приложением (этап 4).

Модульные тесты самого расчёта — в rental_cost/tests.py.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from catalog.models import Bike, BikeType
from rental_cost import CostResult
from rentals.models import Client, Rental

from .services import calculate_rental_cost, estimate_rental, rental_days

PASSWORD = 'test-pass-12345'


def fmt(dt):
    return timezone.localtime(dt).strftime('%Y-%m-%dT%H:%M')


class AdapterTest(TestCase):
    """Приложение передаёт в модуль тип, продолжительность и базовую цену."""

    def setUp(self):
        self.mountain = BikeType(name='Горный', base_price_per_day=Decimal('800'))
        self.start = datetime(2026, 10, 10, 10, 0)

    def test_rental_days_rounds_up(self):
        self.assertEqual(rental_days(self.start, self.start + timedelta(days=2)), 2)
        self.assertEqual(rental_days(self.start, self.start + timedelta(days=2, minutes=1)), 3)
        self.assertEqual(rental_days(self.start, self.start), 0)

    def test_data_passed_to_module(self):
        with mock.patch('pricing.services.calculate_cost', wraps=__import__('rental_cost').calculate_cost) as spy:
            estimate_rental(self.mountain, self.start, self.start + timedelta(days=3, hours=2))
        spy.assert_called_once_with(bike_type='Горный', duration_days=4, base_price_per_day=Decimal('800'))

    def test_module_result_is_used(self):
        fake = CostResult('Горный', 1, Decimal('1'), Decimal('1'), Decimal('0'), Decimal('0'), Decimal('123.45'))
        with mock.patch('pricing.services.calculate_cost', return_value=fake):
            self.assertEqual(calculate_rental_cost(self.mountain, self.start, self.start + timedelta(days=1)),
                             Decimal('123.45'))

    def test_regular_and_discounted(self):
        self.assertEqual(calculate_rental_cost(self.mountain, self.start, self.start + timedelta(days=2)),
                         Decimal('1600.00'))
        self.assertEqual(calculate_rental_cost(self.mountain, self.start, self.start + timedelta(days=3)),
                         Decimal('2160.00'))


class IntegrationTest(TestCase):
    """Стоимость из модуля показывается пользователю и сохраняется в БД."""

    @classmethod
    def setUpTestData(cls):
        cls.city = BikeType.objects.create(name='Городской', base_price_per_day=Decimal('500'))
        cls.bike = Bike.objects.create(model='Stels Navigator', serial_number='SN-1', bike_type=cls.city)
        cls.user = User.objects.create_user('client', password=PASSWORD, role=User.Role.CLIENT)
        cls.profile = Client.objects.create(user=cls.user, last_name='Иванов', first_name='Иван', phone='+79000000001')
        cls.start = timezone.now().replace(second=0, microsecond=0) + timedelta(days=1)

    def setUp(self):
        self.client.force_login(self.user)

    def rent(self, days):
        return self.client.post(reverse('rentals:rental_create'), {
            'bike': self.bike.pk,
            'start_datetime': fmt(self.start),
            'end_datetime': fmt(self.start + timedelta(days=days)),
        })

    def test_regular_rental_cost_saved(self):
        self.rent(2)
        self.assertEqual(Rental.objects.get().total_cost, Decimal('1000.00'))

    def test_discounted_rental_cost_saved(self):
        self.rent(4)  # 500 × 4 = 2000, −10 % = 1800
        self.assertEqual(Rental.objects.get().total_cost, Decimal('1800.00'))

    def test_cost_from_module_is_saved(self):
        fake = CostResult('Городской', 2, Decimal('500'), Decimal('1000'), Decimal('0'), Decimal('0'), Decimal('777.77'))
        with mock.patch('pricing.services.calculate_cost', return_value=fake) as module:
            self.rent(2)
        module.assert_called_once_with(bike_type='Городской', duration_days=2, base_price_per_day=Decimal('500.00'))
        self.assertEqual(Rental.objects.get().total_cost, Decimal('777.77'))

    def test_cost_shown_to_user(self):
        self.rent(4)
        rental = Rental.objects.get()
        page = self.client.get(reverse('rentals:rental_detail', args=[rental.pk]))
        self.assertContains(page, '2000,00 ₽')   # базовая стоимость
        self.assertContains(page, '−200,00 ₽')   # скидка
        self.assertContains(page, '1800,00 ₽')   # итог

    def test_estimate_matches_saved_cost(self):
        end = self.start + timedelta(days=3)
        data = self.client.get(reverse('rentals:rental_estimate'), {
            'bike': self.bike.pk, 'start': fmt(self.start), 'end': fmt(end),
        }).json()
        self.assertTrue(data['ok'])
        self.assertEqual((data['days'], data['discount'], data['total']), (3, True, '1350.00'))
        self.rent(3)
        self.assertEqual(str(Rental.objects.get().total_cost), data['total'])

    def test_module_error_is_shown_not_crash(self):
        from rental_cost import CostCalculationError
        with mock.patch('pricing.services.calculate_cost', side_effect=CostCalculationError('тест')):
            response = self.rent(2)
        self.assertFalse(Rental.objects.exists())
        self.assertContains(response if response.status_code == 200 else self.client.get(response.url),
                            'Не удалось рассчитать стоимость')
