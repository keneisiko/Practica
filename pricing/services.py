"""Связка приложения с модулем расчёта стоимости `rental_cost` (этап 4).

Приложение знает про велосипеды и даты, а модуль — только про
тип велосипеда, продолжительность и базовую цену. Здесь данные из БД
переводятся в исходные данные модуля и передаются ему.
"""

import math

from rental_cost import DISCOUNT_RATE, DISCOUNT_THRESHOLD_DAYS, CostCalculationError, calculate_cost

__all__ = [
    'DISCOUNT_RATE',
    'DISCOUNT_THRESHOLD_DAYS',
    'CostCalculationError',
    'SECONDS_IN_DAY',
    'calculate_rental_cost',
    'estimate_rental',
    'rental_days',
]

SECONDS_IN_DAY = 86400


def rental_days(start_datetime, end_datetime):
    """Количество оплачиваемых суток: неполные сутки округляются вверх. 0 — если интервал некорректный."""
    seconds = (end_datetime - start_datetime).total_seconds()
    if seconds <= 0:
        return 0
    return math.ceil(seconds / SECONDS_IN_DAY)


def estimate_rental(bike_type, start_datetime, end_datetime):
    """Передаёт в модуль тип велосипеда, продолжительность и базовую цену; возвращает CostResult.

    :raises CostCalculationError: если окончание не позже начала или данные типа некорректны
    """
    return calculate_cost(
        bike_type=bike_type.name,
        duration_days=rental_days(start_datetime, end_datetime),
        base_price_per_day=bike_type.base_price_per_day,
    )


def calculate_rental_cost(bike_type, start_datetime, end_datetime):
    """Итоговая стоимость проката для сохранения в БД."""
    return estimate_rental(bike_type, start_datetime, end_datetime).total
