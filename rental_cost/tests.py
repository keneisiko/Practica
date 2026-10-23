"""Модульные тесты расчёта стоимости (без Django и БД).

Запуск отдельно:  python -m unittest rental_cost.tests
"""

import contextlib
import io
import unittest
from decimal import Decimal

from rental_cost import CostCalculationError, calculate_cost, calculate_total
from rental_cost.__main__ import main


class CalculateCostTest(unittest.TestCase):
    def test_regular_rental_without_discount(self):
        r = calculate_cost('Городской', 2, Decimal('500'))
        self.assertEqual(r.total, Decimal('1000.00'))
        self.assertFalse(r.has_discount)
        self.assertEqual(r.discount_amount, Decimal('0.00'))

    def test_one_day(self):
        self.assertEqual(calculate_total('Детский', 1, Decimal('300')), Decimal('300.00'))

    def test_discount_starts_exactly_from_three_days(self):
        r = calculate_cost('Горный', 3, Decimal('800'))
        self.assertTrue(r.has_discount)
        self.assertEqual(r.discount_percent, 10)
        self.assertEqual(r.base_cost, Decimal('2400.00'))
        self.assertEqual(r.discount_amount, Decimal('240.00'))
        self.assertEqual(r.total, Decimal('2160.00'))

    def test_long_rental_with_discount(self):
        self.assertEqual(calculate_total('Электро', 7, Decimal('1500')), Decimal('9450.00'))

    def test_rounding_to_kopecks(self):
        # 333,33 × 3 = 999,99; −10 % = 899,991 → 899,99
        self.assertEqual(calculate_total('Городской', 3, Decimal('333.33')), Decimal('899.99'))

    def test_price_as_string_and_int(self):
        self.assertEqual(calculate_total('Городской', 2, '450.50'), Decimal('901.00'))
        self.assertEqual(calculate_total('Городской', 2, 450), Decimal('900.00'))

    def test_result_keeps_input_data(self):
        r = calculate_cost('  Шоссейный ', 4, Decimal('1000'))
        self.assertEqual((r.bike_type, r.duration_days, r.base_price_per_day), ('Шоссейный', 4, Decimal('1000')))


class InvalidInputTest(unittest.TestCase):
    def assertRejected(self, *args, text):
        with self.assertRaisesRegex(CostCalculationError, text):
            calculate_cost(*args)

    def test_empty_bike_type(self):
        self.assertRejected('', 2, Decimal('500'), text='тип велосипеда')

    def test_zero_or_negative_duration(self):
        self.assertRejected('Городской', 0, Decimal('500'), text='не меньше 1')
        self.assertRejected('Городской', -2, Decimal('500'), text='не меньше 1')

    def test_fractional_duration(self):
        self.assertRejected('Городской', 1.5, Decimal('500'), text='целым числом')

    def test_bad_price(self):
        self.assertRejected('Городской', 2, Decimal('0'), text='больше нуля')
        self.assertRejected('Городской', 2, 'abc', text='ожидается число')


class CommandLineTest(unittest.TestCase):
    def test_cli_ok_and_error(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(main(['--type', 'Горный', '--days', '4', '--price', '800']), 0)
            self.assertEqual(main(['--type', 'Горный', '--days', '0', '--price', '800']), 1)
        self.assertIn('Итого: 2880.00 ₽', out.getvalue())
        self.assertIn('не меньше 1', err.getvalue())
