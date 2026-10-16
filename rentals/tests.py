from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from catalog.models import Bike, BikeType

from .models import Client, Rental

PASSWORD = 'test-pass-12345'


def fmt(dt):
    """Формат поля <input type="datetime-local">."""
    return timezone.localtime(dt).strftime('%Y-%m-%dT%H:%M')


class RentalTestData(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.city = BikeType.objects.create(name='Городской', base_price_per_day=Decimal('500'))
        cls.bike = Bike.objects.create(model='Stels Navigator', serial_number='SN-1', bike_type=cls.city)
        cls.busy_bike = Bike.objects.create(
            model='Trek Marlin', serial_number='SN-2', bike_type=cls.city, status=Bike.Status.RENTED
        )

        cls.client_user = User.objects.create_user('client', password=PASSWORD, role=User.Role.CLIENT)
        cls.client_profile = Client.objects.create(
            user=cls.client_user, last_name='Иванов', first_name='Иван', phone='+79000000001'
        )
        cls.other_client = Client.objects.create(last_name='Петров', first_name='Пётр', phone='+79000000002')
        cls.manager = User.objects.create_user('manager', password=PASSWORD, role=User.Role.MANAGER)
        cls.admin = User.objects.create_user('boss', password=PASSWORD, role=User.Role.ADMIN)
        cls.visitor = User.objects.create_user('guest', password=PASSWORD, role=User.Role.VISITOR)

        cls.start = timezone.now().replace(second=0, microsecond=0) + timedelta(days=1)

    def make_rental(self, client=None, bike=None, status=Rental.Status.ACTIVE):
        return Rental.objects.create(
            client=client or self.other_client,
            bike=bike or self.busy_bike,
            start_datetime=self.start,
            end_datetime=self.start + timedelta(days=1),
            total_cost=Decimal('500'),
            status=status,
        )


class RentalCreateTest(RentalTestData):
    url = reverse('rentals:rental_create')

    def post(self, **data):
        payload = {'bike': self.bike.pk, 'start_datetime': fmt(self.start), 'end_datetime': fmt(self.start + timedelta(days=2))}
        payload.update(data)
        return self.client.post(self.url, {k: v for k, v in payload.items() if v is not None})

    def test_client_creates_own_rental_with_calculated_cost(self):
        self.client.force_login(self.client_user)
        response = self.post()
        rental = Rental.objects.get()
        self.assertRedirects(response, reverse('rentals:rental_detail', args=[rental.pk]))
        self.assertEqual(rental.client, self.client_profile)
        self.assertEqual(rental.total_cost, Decimal('1000.00'))  # 2 суток × 500
        self.assertEqual(rental.created_by, self.client_user)
        self.bike.refresh_from_db()
        self.assertEqual(self.bike.status, Bike.Status.RENTED)

    def test_discount_from_three_days(self):
        self.client.force_login(self.client_user)
        self.post(end_datetime=fmt(self.start + timedelta(days=3)))
        self.assertEqual(Rental.objects.get().total_cost, Decimal('1350.00'))  # 1500 − 10 %

    def test_client_cannot_choose_other_client(self):
        self.client.force_login(self.client_user)
        self.post(client=self.other_client.pk)
        self.assertEqual(Rental.objects.get().client, self.client_profile)

    def test_manager_creates_rental_for_client(self):
        self.client.force_login(self.manager)
        self.post(client=self.other_client.pk)
        self.assertEqual(Rental.objects.get().client, self.other_client)

    def test_manager_must_choose_client(self):
        self.client.force_login(self.manager)
        response = self.post()
        self.assertContains(response, 'Выберите клиента.')
        self.assertFalse(Rental.objects.exists())

    def test_bike_is_required(self):
        self.client.force_login(self.client_user)
        response = self.post(bike='')
        self.assertContains(response, 'Выберите велосипед.')

    def test_unavailable_bike_cannot_be_chosen(self):
        self.client.force_login(self.client_user)
        response = self.post(bike=self.busy_bike.pk)
        self.assertContains(response, 'недоступен для проката')
        self.assertFalse(Rental.objects.exists())

    def test_end_must_be_after_start(self):
        self.client.force_login(self.client_user)
        response = self.post(end_datetime=fmt(self.start - timedelta(hours=1)))
        self.assertContains(response, 'должны быть позже начала')
        self.assertFalse(Rental.objects.exists())

    def test_nonexistent_client_rejected(self):
        self.client.force_login(self.manager)
        response = self.post(client=999999)
        self.assertContains(response, 'Такого клиента нет.')

    def test_user_without_client_profile_gets_message(self):
        orphan = User.objects.create_user('orphan', password=PASSWORD, role=User.Role.CLIENT)
        self.client.force_login(orphan)
        response = self.post()
        self.assertContains(response, 'не привязан профиль клиента')
        self.assertFalse(Rental.objects.exists())

    def test_visitor_and_anonymous_cannot_rent(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.url}")
        self.client.force_login(self.visitor)
        self.assertEqual(self.client.get(self.url).status_code, 403)


class RentalListTest(RentalTestData):
    def test_client_sees_only_own_rentals(self):
        own = self.make_rental(client=self.client_profile)
        foreign = self.make_rental()
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('rentals:rental_list'))
        self.assertEqual(list(response.context['rentals']), [own])
        self.assertEqual(self.client.get(reverse('rentals:rental_detail', args=[foreign.pk])).status_code, 404)

    def test_manager_sees_all_rentals(self):
        self.make_rental(client=self.client_profile)
        self.make_rental()
        self.client.force_login(self.manager)
        response = self.client.get(reverse('rentals:rental_list'))
        self.assertEqual(len(response.context['rentals']), 2)

    def test_status_filter(self):
        self.make_rental(status=Rental.Status.COMPLETED)
        self.make_rental()
        self.client.force_login(self.manager)
        response = self.client.get(reverse('rentals:rental_list'), {'status': 'completed'})
        self.assertEqual(len(response.context['rentals']), 1)


class RentalCompleteTest(RentalTestData):
    def test_manager_completes_rental_and_bike_becomes_available(self):
        rental = self.make_rental()
        self.client.force_login(self.manager)
        url = reverse('rentals:rental_complete', args=[rental.pk])
        self.assertContains(self.client.get(url), 'Да, завершить')  # сначала подтверждение
        self.client.post(url)
        rental.refresh_from_db()
        self.busy_bike.refresh_from_db()
        self.assertEqual(rental.status, Rental.Status.COMPLETED)
        self.assertEqual(self.busy_bike.status, Bike.Status.AVAILABLE)

    def test_completed_rental_cannot_be_completed_again(self):
        rental = self.make_rental(status=Rental.Status.COMPLETED)
        self.client.force_login(self.manager)
        response = self.client.post(reverse('rentals:rental_complete', args=[rental.pk]), follow=True)
        self.assertContains(response, 'Завершить можно только активный прокат')

    def test_client_cannot_complete(self):
        rental = self.make_rental(client=self.client_profile)
        self.client.force_login(self.client_user)
        response = self.client.post(reverse('rentals:rental_complete', args=[rental.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'только менеджерам и администраторам', status_code=403)


class AdminFunctionsTest(RentalTestData):
    def test_admin_edits_rental_and_cost_is_recalculated(self):
        rental = self.make_rental()
        self.client.force_login(self.admin)
        response = self.client.post(reverse('rentals:rental_edit', args=[rental.pk]), {
            'client': self.client_profile.pk,
            'bike': self.busy_bike.pk,
            'start_datetime': fmt(self.start),
            'end_datetime': fmt(self.start + timedelta(days=4)),
            'status': Rental.Status.ACTIVE,
        })
        self.assertRedirects(response, reverse('rentals:rental_detail', args=[rental.pk]))
        rental.refresh_from_db()
        self.assertEqual(rental.client, self.client_profile)
        self.assertEqual(rental.total_cost, Decimal('1800.00'))

    def test_admin_moves_rental_to_another_bike(self):
        rental = self.make_rental()
        self.client.force_login(self.admin)
        self.client.post(reverse('rentals:rental_edit', args=[rental.pk]), {
            'client': self.other_client.pk,
            'bike': self.bike.pk,
            'start_datetime': fmt(self.start),
            'end_datetime': fmt(self.start + timedelta(days=1)),
            'status': Rental.Status.ACTIVE,
        })
        self.bike.refresh_from_db()
        self.busy_bike.refresh_from_db()
        self.assertEqual(self.bike.status, Bike.Status.RENTED)
        self.assertEqual(self.busy_bike.status, Bike.Status.AVAILABLE)

    def test_admin_adds_and_edits_client(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('rentals:client_create'), {
            'last_name': 'Сидоров', 'first_name': 'Сидор', 'phone': '+7 900 000-00-99', 'email': '',
        })
        client = Client.objects.get(last_name='Сидоров')
        self.assertEqual(client.phone, '+79000000099')
        self.assertIsNone(client.email)
        self.client.post(reverse('rentals:client_edit', args=[client.pk]), {
            'last_name': 'Сидоров', 'first_name': 'Семён', 'phone': '+79000000099', 'email': 's@example.com',
        })
        client.refresh_from_db()
        self.assertEqual(client.first_name, 'Семён')

    def test_duplicate_phone_rejected(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('rentals:client_create'), {
            'last_name': 'Дубль', 'first_name': 'Д', 'phone': self.other_client.phone, 'email': '',
        })
        self.assertContains(response, 'Клиент с таким телефоном уже есть.')

    def test_manager_has_no_admin_functions(self):
        rental = self.make_rental()
        self.client.force_login(self.manager)
        for url in (
            reverse('rentals:rental_edit', args=[rental.pk]),
            reverse('rentals:client_list'),
            reverse('rentals:client_create'),
            reverse('catalog:bike_create'),
            reverse('catalog:bike_edit', args=[self.bike.pk]),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)
                self.assertContains(response, 'только администратору', status_code=403)


class EstimateTest(RentalTestData):
    def test_estimate_returns_same_cost_as_service(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('rentals:rental_estimate'), {
            'bike': self.bike.pk, 'start': fmt(self.start), 'end': fmt(self.start + timedelta(days=3)),
        })
        self.assertEqual(response.json()['total'], '1350.00')
        self.assertTrue(response.json()['discount'])

    def test_estimate_rejects_bad_period(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('rentals:rental_estimate'), {
            'bike': self.bike.pk, 'start': fmt(self.start), 'end': fmt(self.start),
        })
        self.assertFalse(response.json()['ok'])
