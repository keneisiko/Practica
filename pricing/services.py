import math
from decimal import ROUND_HALF_UP, Decimal

DISCOUNT_THRESHOLD_DAYS = 3
DISCOUNT_RATE = Decimal('0.10')
SECONDS_IN_DAY = 86400


def rental_days(start_datetime, end_datetime):
    """Количество оплачиваемых суток: неполные сутки округляются вверх. 0 — если интервал некорректный."""
    seconds = (end_datetime - start_datetime).total_seconds()
    if seconds <= 0:
        return 0
    return math.ceil(seconds / SECONDS_IN_DAY)


def calculate_rental_cost(bike_type, start_datetime, end_datetime):
    """Стоимость = базовая цена типа за сутки × количество суток, от 3 суток — скидка 10 %."""
    days = rental_days(start_datetime, end_datetime)
    if days == 0:
        return Decimal('0')
    cost = bike_type.base_price_per_day * days
    if days >= DISCOUNT_THRESHOLD_DAYS:
        cost = cost * (Decimal('1') - DISCOUNT_RATE)
    return cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
