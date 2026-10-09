import math
from decimal import Decimal, ROUND_HALF_UP

DISCOUNT_THRESHOLD_DAYS = 3
DISCOUNT_RATE = Decimal('0.10')

def calculate_rental_cost(bike_type, start_datetime, end_datetime):
    delta = end_datetime - start_datetime
    if delta.total_seconds() <= 0:
        return Decimal('0')  # Если время аренды отрицательное или нулевое, стоимость равна 0
    delta = end_datetime - start_datetime
    days = math.ceil(delta.total_seconds() / 86400)
    base_price_per_day = bike_type.base_price_per_day   # ← берём из типа
    cost = base_price_per_day * days                     # ← базовая стоимость
    if days >= DISCOUNT_THRESHOLD_DAYS:
        cost = cost * (Decimal('1') - DISCOUNT_RATE)
    return cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)  # Округление до двух знаков после запятой