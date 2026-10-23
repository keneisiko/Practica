"""Модуль расчёта стоимости проката велосипеда (этап 4).

Независимый программный модуль: не использует Django и базу данных,
поэтому его можно подключить к любому приложению или запустить из командной строки.

    >>> from decimal import Decimal
    >>> from rental_cost import calculate_cost
    >>> calculate_cost('Городской', 4, Decimal('500')).total
    Decimal('1800.00')
"""

from .calculator import (
    DISCOUNT_RATE,
    DISCOUNT_THRESHOLD_DAYS,
    CostCalculationError,
    CostResult,
    calculate_cost,
    calculate_total,
)

__all__ = [
    'DISCOUNT_RATE',
    'DISCOUNT_THRESHOLD_DAYS',
    'CostCalculationError',
    'CostResult',
    'calculate_cost',
    'calculate_total',
]
