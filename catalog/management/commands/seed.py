from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from catalog.models import BikeType, Bike
from rentals.models import Client, Rental


class Command(BaseCommand):
    help = 'Заполняет БД тестовыми данными'

    def handle(self, *args, **options):
        # Типы велосипедов
        types_data = [
            ('Горный', Decimal('800')),
            ('Шоссейный', Decimal('1000')),
            ('Городской', Decimal('500')),
            ('Детский', Decimal('300')),
            ('Электровелосипед', Decimal('1500')),
        ]
        for name, price in types_data:
            BikeType.objects.get_or_create(
                name=name,
                defaults={'base_price_per_day': price},
            )

        mountain = BikeType.objects.get(name='Горный')
        road = BikeType.objects.get(name='Шоссейный')
        city = BikeType.objects.get(name='Городской')
        kids = BikeType.objects.get(name='Детский')
        electric = BikeType.objects.get(name='Электровелосипед')

        # Велосипеды
        bikes_data = [
            ('Trek Marlin 5', 'SN-0001', mountain, 'available'),
            ('Trek Marlin 6', 'SN-0002', mountain, 'available'),
            ('Giant Talon 3', 'SN-0003', mountain, 'rented'),
            ('Scott Aspect 940', 'SN-0004', mountain, 'available'),
            ('Merida Big Nine 100', 'SN-0005', mountain, 'maintenance'),
            ('Cannondale Synapse', 'SN-0006', road, 'available'),
            ('Specialized Allez', 'SN-0007', road, 'rented'),
            ('Pinarello GAN', 'SN-0008', road, 'available'),
            ('Stels Navigator 350', 'SN-0009', city, 'available'),
            ('Forward Apache 1.0', 'SN-0010', city, 'available'),
            ('Stels Navigator 500', 'SN-0011', city, 'rented'),
            ('Btwin Original 100', 'SN-0012', city, 'available'),
            ('Stels Junior', 'SN-0013', kids, 'available'),
            ('Merida Matts J20', 'SN-0014', kids, 'available'),
            ('Haibike SDURO', 'SN-0015', electric, 'available'),
            ('Cube Reaction Hybrid', 'SN-0016', electric, 'rented'),
            ('Giant Escape E+', 'SN-0017', electric, 'available'),
        ]
        for model, sn, btype, status in bikes_data:
            Bike.objects.get_or_create(
                serial_number=sn,
                defaults={
                    'model': model,
                    'bike_type': btype,
                    'status': status,
                },
            )

        # Клиенты
        clients_data = [
            ('Иванов', 'Иван', '+79000000001', 'ivanov@mail.ru'),
            ('Петров', 'Пётр', '+79000000002', 'petrov@mail.ru'),
            ('Сидоров', 'Сидор', '+79000000003', 'sidorov@mail.ru'),
            ('Кузнецов', 'Алексей', '+79000000004', 'kuznetsov@mail.ru'),
            ('Смирнова', 'Анна', '+79000000005', 'smirnova@mail.ru'),
            ('Попов', 'Дмитрий', '+79000000006', 'popov@mail.ru'),
            ('Васильев', 'Максим', '+79000000007', 'vasiliev@mail.ru'),
            ('Новикова', 'Елена', '+79000000008', 'novikova@mail.ru'),
            ('Морозов', 'Артём', '+79000000009', 'morozov@mail.ru'),
            ('Волкова', 'Ольга', '+79000000010', 'volkova@mail.ru'),
            ('Соколов', 'Никита', '+79000000011', 'sokolov@mail.ru'),
            ('Лебедева', 'Мария', '+79000000012', 'lebedeva@mail.ru'),
            ('Козлов', 'Егор', '+79000000013', 'kozlov@mail.ru'),
            ('Орлова', 'Дарья', '+79000000014', 'orlova@mail.ru'),
            ('Никитин', 'Роман', '+79000000015', 'nikitin@mail.ru'),
            ('Фёдорова', 'Виктория', '+79000000016', 'fedorova@mail.ru'),
            ('Захаров', 'Кирилл', '+79000000017', 'zakharov@mail.ru'),
            ('Белова', 'Полина', '+79000000018', 'belova@mail.ru'),
            ('Медведев', 'Андрей', '+79000000019', 'medvedev@mail.ru'),
            ('Ершова', 'София', '+79000000020', 'ershova@mail.ru'),
            ('Тихонов', 'Илья', '+79000000021', 'tikhonov@mail.ru'),
            ('Громова', 'Алиса', '+79000000022', 'gromova@mail.ru'),
            ('Крылов', 'Матвей', '+79000000023', 'krylov@mail.ru'),
            ('Романова', 'Ксения', '+79000000024', 'romanova@mail.ru'),
            ('Богданов', 'Тимофей', '+79000000025', 'bogdanov@mail.ru'),
        ]
        for last, first, phone, email in clients_data:
            Client.objects.get_or_create(
                phone=phone,
                defaults={
                    'last_name': last,
                    'first_name': first,
                    'email': email,
                },
            )

        # Прокаты — пересоздаём, чтобы не было дубликатов
        Rental.objects.all().delete()

        now = timezone.now()
        clients = list(Client.objects.all())
        bikes = list(Bike.objects.all())

        rentals_data = [
            # (client_idx, bike_idx, start_offset_days, end_offset_days, status)
            (0, 2, -30, -28, 'completed'),
            (1, 6, -25, -24, 'completed'),
            (2, 10, -20, -18, 'completed'),
            (3, 15, -15, -12, 'completed'),
            (4, 0, -12, -11, 'completed'),
            (5, 8, -10, -9, 'completed'),
            (6, 12, -8, -7, 'completed'),
            (7, 14, -5, -3, 'completed'),
            (8, 2, -1, 1, 'active'),
            (9, 6, -1, 1, 'active'),
            (10, 10, 0, 2, 'active'),
            (11, 15, -1, 1, 'active'),
            (12, 0, 0, 1, 'active'),
            (13, 5, -5, -4, 'cancelled'),
            (14, 8, -3, -2, 'cancelled'),
            (15, 16, -1, 2, 'active'),
        ]

        for c_idx, b_idx, start_off, end_off, status in rentals_data:
            client = clients[c_idx]
            bike = bikes[b_idx]
            start = now + timedelta(days=start_off)
            end = now + timedelta(days=end_off)
            days = max(1, (end - start).days)
            cost = bike.bike_type.base_price_per_day * days
            if days >= 3:
                cost = cost * Decimal('0.9')
            cost = cost.quantize(Decimal('0.01'))

            Rental.objects.create(
                client=client,
                bike=bike,
                start_datetime=start,
                end_datetime=end,
                total_cost=cost,
                status=status,
            )

            if status == 'active':
                bike.status = 'rented'
                bike.save()

        self.stdout.write(self.style.SUCCESS(
            f'БД заполнена: {BikeType.objects.count()} типов, '
            f'{Bike.objects.count()} велосипедов, '
            f'{Client.objects.count()} клиентов, '
            f'{Rental.objects.count()} прокатов.'
        ))