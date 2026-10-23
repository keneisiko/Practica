"""Бизнес-операции с прокатами. Вьюхи только вызывают эти функции и показывают результат."""

from django.db import transaction

from catalog.models import Bike
from pricing.services import calculate_rental_cost

from .models import Rental


class RentalError(Exception):
    """Операцию нельзя выполнить. Текст исключения показывается пользователю."""


def _lock_bike(bike_id):
    # select_for_update блокирует строку велосипеда до конца транзакции:
    # два одновременных оформления не займут один велосипед.
    return Bike.objects.select_for_update().select_related('bike_type').get(pk=bike_id)


def _release_bike_if_free(bike):
    """Делает велосипед доступным, если у него не осталось активных прокатов."""
    active = Rental.objects.filter(bike=bike, status=Rental.Status.ACTIVE)
    if bike.status == Bike.Status.RENTED and not active.exists():
        bike.status = Bike.Status.AVAILABLE
        bike.save(update_fields=['status', 'updated_at'])


@transaction.atomic
def create_rental(*, client, bike, start_datetime, end_datetime, created_by):
    bike = _lock_bike(bike.pk)
    if bike.status != Bike.Status.AVAILABLE:
        raise RentalError('Этот велосипед только что стал недоступен — выберите другой.')
    rental = Rental.objects.create(
        client=client,
        bike=bike,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        total_cost=calculate_rental_cost(bike.bike_type, start_datetime, end_datetime),
        status=Rental.Status.ACTIVE,
        created_by=created_by,
    )
    bike.status = Bike.Status.RENTED
    bike.save(update_fields=['status', 'updated_at'])
    return rental


@transaction.atomic
def complete_rental(rental):
    rental = Rental.objects.select_for_update().get(pk=rental.pk)
    if rental.status != Rental.Status.ACTIVE:
        raise RentalError(f'Завершить можно только активный прокат, а этот — «{rental.get_status_display()}».')
    rental.status = Rental.Status.COMPLETED
    rental.save(update_fields=['status'])
    _release_bike_if_free(_lock_bike(rental.bike_id))
    return rental


@transaction.atomic
def cancel_rental(rental):
    """Отмена проката: статус «Отменён», запись остаётся в БД, велосипед снова доступен.

    Завершённый прокат отменить нельзя, повторная отмена тоже запрещена.
    """
    rental = Rental.objects.select_for_update().get(pk=rental.pk)
    if rental.status == Rental.Status.COMPLETED:
        raise RentalError('Завершённый прокат отменить нельзя.')
    if rental.status == Rental.Status.CANCELLED:
        raise RentalError('Этот прокат уже отменён.')
    rental.status = Rental.Status.CANCELLED
    rental.save(update_fields=['status'])
    _release_bike_if_free(_lock_bike(rental.bike_id))
    return rental


@transaction.atomic
def update_rental(rental, *, client, bike, start_datetime, end_datetime, status):
    """Редактирование проката администратором: пересчитывает стоимость и статусы велосипедов."""
    rental = Rental.objects.select_for_update().get(pk=rental.pk)
    old_bike_id, old_status = rental.bike_id, rental.status
    new_bike = _lock_bike(bike.pk)
    becomes_active = status == Rental.Status.ACTIVE
    takes_new_bike = becomes_active and (new_bike.pk != old_bike_id or old_status != Rental.Status.ACTIVE)

    if takes_new_bike and new_bike.status != Bike.Status.AVAILABLE:
        raise RentalError('Выбранный велосипед сейчас недоступен — активный прокат на него оформить нельзя.')

    rental.client = client
    rental.bike = new_bike
    rental.start_datetime = start_datetime
    rental.end_datetime = end_datetime
    rental.status = status
    rental.total_cost = calculate_rental_cost(new_bike.bike_type, start_datetime, end_datetime)
    rental.save()

    if takes_new_bike:
        new_bike.status = Bike.Status.RENTED
        new_bike.save(update_fields=['status', 'updated_at'])
    if old_status == Rental.Status.ACTIVE and (new_bike.pk != old_bike_id or not becomes_active):
        # прокат уже сохранён с новым велосипедом/статусом, поэтому в выборке активных его нет
        _release_bike_if_free(_lock_bike(old_bike_id))
    return rental
