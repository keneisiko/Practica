"""Запуск модуля из командной строки:

    python -m rental_cost --type Горный --days 4 --price 800
"""

import argparse
import sys

from .calculator import CostCalculationError, calculate_cost


def main(argv=None):
    parser = argparse.ArgumentParser(description='Расчёт стоимости проката велосипеда')
    parser.add_argument('--type', required=True, help='тип велосипеда')
    parser.add_argument('--days', required=True, type=int, help='продолжительность, суток')
    parser.add_argument('--price', required=True, help='базовая стоимость суток, ₽')
    args = parser.parse_args(argv)
    try:
        r = calculate_cost(args.type, args.days, args.price)
    except CostCalculationError as exc:
        print(f'Ошибка: {exc}', file=sys.stderr)
        return 1
    print(f'Тип: {r.bike_type}')
    print(f'{r.base_price_per_day} ₽ × {r.duration_days} сут. = {r.base_cost} ₽')
    if r.has_discount:
        print(f'Скидка {r.discount_percent} %: −{r.discount_amount} ₽')
    print(f'Итого: {r.total} ₽')
    return 0


if __name__ == '__main__':
    sys.exit(main())
