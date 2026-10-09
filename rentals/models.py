from django.db import models
import math
from django.conf import settings
from django.core.exceptions import ValidationError


class Client(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='client_profile',
        verbose_name='Пользователь',
    )
    last_name = models.CharField(
        max_length=50,
        verbose_name='Фамилия',
    )
    first_name = models.CharField(
        max_length=50,
        verbose_name='Имя',
    )
    phone = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Номер телефона',
    )
    email = models.EmailField(
        blank=True,
        null=True,
        unique=True,
        verbose_name='Email',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ('last_name', 'first_name')

    def __str__(self):
        return f'{self.last_name} {self.first_name}'

    @property
    def full_name(self):
        return f'{self.last_name} {self.first_name}'


class RentalManager(models.Manager):
    def active_rentals(self):
        return self.filter(status='active')

    def completed_rentals(self):
        return self.filter(status='completed')

    def cancelled_rentals(self):
        return self.filter(status='cancelled')


class Rental(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Активна'
        COMPLETED = 'completed', 'Завершена'
        CANCELLED = 'cancelled', 'Отменена'

    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='rentals',
        verbose_name='Клиент',
    )
    bike = models.ForeignKey(
        'catalog.Bike',
        on_delete=models.PROTECT,
        related_name='rentals',
        verbose_name='Велосипед',
    )
    start_datetime = models.DateTimeField(
        verbose_name='Дата начала',
    )
    end_datetime = models.DateTimeField(
        verbose_name='Дата окончания',
    )
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Общая стоимость',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='Статус',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_rentals',
        verbose_name='Создано пользователем',
    )

    objects = RentalManager()

    class Meta:
        verbose_name = 'Аренда'
        verbose_name_plural = 'Аренды'
        ordering = ('-start_datetime',)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_datetime__gt=models.F('start_datetime')),
                name='rental_dates_valid',
            ),
            models.CheckConstraint(
                condition=models.Q(total_cost__gte=0),
                name='rental_cost_non_negative',
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=['active', 'completed', 'cancelled']),
                name='rental_status_valid',
            ),
        ]
        indexes = [
            models.Index(fields=['client']),
            models.Index(fields=['bike']),
            models.Index(fields=['start_datetime']),
            models.Index(fields=['end_datetime']),
        ]

    @property
    def duration_days(self):
        delta = self.end_datetime - self.start_datetime
        if delta.total_seconds() <= 0:
            return 0
        return math.ceil(delta.total_seconds() / 86400)

    def clean(self):
        if self.end_datetime <= self.start_datetime:
            raise ValidationError('Дата окончания должна быть позже даты начала.')

    def cancel(self):
        if self.status == self.Status.COMPLETED:
            raise ValidationError('Невозможно отменить завершенную аренду.')
        elif self.status == self.Status.CANCELLED:
            raise ValidationError('Аренда уже отменена.')
        else:
            self.status = self.Status.CANCELLED
            self.save()

    def complete(self):
        if self.status == self.Status.CANCELLED:
            raise ValidationError('Невозможно завершить отмененную аренду.')
        elif self.status == self.Status.COMPLETED:
            raise ValidationError('Аренда уже завершена.')
        else:
            self.status = self.Status.COMPLETED
            self.save()

    def __str__(self):
        return f'Прокат #{self.pk} — {self.client} — {self.bike}'