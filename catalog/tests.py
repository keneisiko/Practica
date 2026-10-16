from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Bike, BikeType


class CatalogTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.mountain = BikeType.objects.create(name='Горный', base_price_per_day=Decimal('800'))
        cls.city = BikeType.objects.create(name='Городской', base_price_per_day=Decimal('500'))
        cls.trek = Bike.objects.create(model='Trek Marlin 5', serial_number='SN-0001', bike_type=cls.mountain)
        cls.stels = Bike.objects.create(
            model='Stels Navigator', serial_number='SN-0002', bike_type=cls.city, status=Bike.Status.RENTED
        )
        cls.client_user = User.objects.create_user('client', password='x-12345678', role=User.Role.CLIENT)
        cls.visitor = User.objects.create_user('guest', password='x-12345678', role=User.Role.VISITOR)
        cls.admin = User.objects.create_user('boss', password='x-12345678', role=User.Role.ADMIN)

    def test_catalog_shows_model_type_price_and_status(self):
        response = self.client.get(reverse('catalog:bike_list'))
        for text in ('Trek Marlin 5', 'Горный', '800 ₽', 'Доступен', 'В прокате'):
            self.assertContains(response, text)

    def test_visitor_has_no_search_and_no_rent_button(self):
        self.client.force_login(self.visitor)
        response = self.client.get(reverse('catalog:bike_list'), {'q': 'Trek'})
        self.assertFalse(response.context['can_search'])
        self.assertEqual(len(response.context['bikes']), 2)  # фильтр проигнорирован
        self.assertNotContains(response, 'Оформить</a>')

    def test_client_can_search_filter_and_sort(self):
        self.client.force_login(self.client_user)
        url = reverse('catalog:bike_list')
        self.assertEqual(list(self.client.get(url, {'q': 'trek'}).context['bikes']), [self.trek])
        self.assertEqual(list(self.client.get(url, {'status': 'rented'}).context['bikes']), [self.stels])
        self.assertEqual(list(self.client.get(url, {'bike_type': self.city.pk}).context['bikes']), [self.stels])
        by_price = self.client.get(url, {'sort': 'bike_type__base_price_per_day'}).context['bikes']
        self.assertEqual(list(by_price), [self.stels, self.trek])

    def test_rented_bike_has_disabled_button(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('catalog:bike_detail', args=[self.stels.pk]))
        self.assertContains(response, 'Велосипед недоступен для проката')

    def test_admin_adds_bike(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('catalog:bike_create'), {
            'model': 'Giant Talon', 'serial_number': 'sn-0003', 'bike_type': self.mountain.pk,
            'status': Bike.Status.AVAILABLE, 'description': '',
        })
        self.assertTrue(Bike.objects.filter(serial_number='SN-0003').exists())

    def test_rented_status_cannot_be_set_manually(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('catalog:bike_edit', args=[self.trek.pk]), {
            'model': self.trek.model, 'serial_number': self.trek.serial_number,
            'bike_type': self.mountain.pk, 'status': Bike.Status.RENTED, 'description': '',
        })
        self.assertContains(response, 'ставится автоматически')

    def test_client_cannot_add_bike(self):
        self.client.force_login(self.client_user)
        self.assertEqual(self.client.get(reverse('catalog:bike_create')).status_code, 403)
