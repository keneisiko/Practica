"""Расчёт итоговой стоимости проката.

Входные данные:  тип велосипеда, продолжительность проката (в сутках), базовая стоимость суток.
Результат:       итоговая стоимость с учётом скидки 10 % при прокате от 3 суток.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

DISCOUNT_THRESHOLD_DAYS = 3        # с какого количества суток действует скидка
DISCOUNT_RATE = Decimal('0.10')    # размер скидки — 10 %
_KOPECK = Decimal('0.01')


class CostCalculationError(ValueError):
    """Исходные данные некорректны. Текст исключения понятен пользователю."""


@dataclass(frozen=True)
class CostResult:
    """Результат расчёта: итог и промежуточные величины для показа пользователю."""

    bike_type: str
    duration_days: int
    base_price_per_day: Decimal
    base_cost: Decimal        # базовая цена × сутки
    discount_rate: Decimal    # 0 или 0.10
    discount_amount: Decimal  # сумма скидки в рублях
    total: Decimal            # итоговая стоимость

    @property
    def has_discount(self):
        return self.discount_rate > 0

    @property
    def discount_percent(self):
        return int(self.discount_rate * 100)


def _to_money(value, field):
    if isinstance(value, float):
        value = str(value)  # избегаем неточности float: 0.1 → '0.1'
    try:
        money = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise CostCalculationError(f'{field}: ожидается число, получено {value!r}.') from None
    if not money.is_finite():
        raise CostCalculationError(f'{field}: ожидается конечное число.')
    return money


def calculate_cost(bike_type, duration_days, base_price_per_day):
    """Рассчитывает стоимость проката.

    :param bike_type: тип велосипеда (название, например «Горный»)
    :param duration_days: продолжительность проката в сутках, целое число ≥ 1
    :param base_price_per_day: базовая стоимость суток для этого типа, > 0
    :return: CostResult, итоговая стоимость — в поле ``total``
    :raises CostCalculationError: если исходные данные некорректны
    """
    bike_type = str(bike_type or '').strip()
    if not bike_type:
        raise CostCalculationError('Не указан тип велосипеда.')

    if isinstance(duration_days, bool) or not isinstance(duration_days, int):
        raise CostCalculationError('Продолжительность проката должна быть целым числом суток.')
    if duration_days < 1:
        raise CostCalculationError('Продолжительность проката должна быть не меньше 1 суток.')

    price = _to_money(base_price_per_day, 'Базовая стоимость')
    if price <= 0:
        raise CostCalculationError('Базовая стоимость суток должна быть больше нуля.')

    base_cost = (price * duration_days).quantize(_KOPECK, rounding=ROUND_HALF_UP)
    rate = DISCOUNT_RATE if duration_days >= DISCOUNT_THRESHOLD_DAYS else Decimal('0')
    total = (price * duration_days * (Decimal('1') - rate)).quantize(_KOPECK, rounding=ROUND_HALF_UP)

    return CostResult(
        bike_type=bike_type,
        duration_days=duration_days,
        base_price_per_day=price,
        base_cost=base_cost,
        discount_rate=rate,
        discount_amount=base_cost - total,
        total=total,
    )


def calculate_total(bike_type, duration_days, base_price_per_day):
    """Короткий вариант: возвращает только итоговую стоимость (Decimal)."""
    return calculate_cost(bike_type, duration_days, base_price_per_day).total
