from django.test import TestCase
from .services import calculate_rental_cost
from decimal import Decimal
import datetime

# Create your tests here.

class FakeBikeType:
    base_price_per_day = Decimal('800')

class RentalCostTest(TestCase):
    def test_simple_rental(self):
        result = calculate_rental_cost(
            bike_type=FakeBikeType(),
            start_datetime=datetime.datetime(2026, 10, 10, 10, 0),
            end_datetime=datetime.datetime(2026, 10, 12, 10, 0),
        )
        self.assertEqual(result, Decimal('1600'))
    def test_discounted_rental(self):
        result = calculate_rental_cost(
            bike_type=FakeBikeType(),
            start_datetime=datetime.datetime(2026, 10, 10, 10, 0),
            end_datetime=datetime.datetime(2026, 10, 13, 10, 0),
        )
        self.assertEqual(result, Decimal('2160.00'))  # 4 days * 800 = 3200 - 10% = 2880
    def test_two_day_duration_rental(self):
        result = calculate_rental_cost(
            bike_type=FakeBikeType(),
            start_datetime=datetime.datetime(2026, 10, 10, 10, 0),
            end_datetime=datetime.datetime(2026, 10, 12, 9, 59),
        )
        self.assertEqual(result, Decimal('1600'))  # Still counts as 2 days
    def test_zero_duration_rental(self):
        result = calculate_rental_cost(
            bike_type=FakeBikeType(),
            start_datetime=datetime.datetime(2026, 10, 10, 10, 0),
            end_datetime=datetime.datetime(2026, 10, 10, 10, 0),
        )
        self.assertEqual(result, Decimal('0'))  # Zero duration should cost 0
    