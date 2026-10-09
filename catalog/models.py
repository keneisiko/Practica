from django.db import models
# Create your models here.


class BikeType(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Название'
    )
    base_price_per_day = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Базовая цена за сутки',
    )
    class Meta:
        verbose_name = 'Тип велосипеда'
        verbose_name_plural = 'Типы велосипедов'
        ordering = ('name',)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(base_price_per_day__gt=0),
                name='bike_type_price_positive',
            ),
        ]
    def __str__(self):
        return self.name
class Bike(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Доступен'
        RENTED = 'rented', 'В прокате'
        MAINTENANCE = 'maintenance', 'Обслуживание'
    model = models.CharField(
        max_length=100,
        verbose_name='Модель',
    )
    serial_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Серийный номер',
    )
    bike_type = models.ForeignKey(
        BikeType,
        on_delete=models.PROTECT,
        related_name='bikes',
        verbose_name='Тип',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
        verbose_name='Статус',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создан',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлён',
    )
    class Meta:
        verbose_name='Велосипед'
        verbose_name_plural='Велосипеды'
        ordering = ('model',)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=['available', 'rented', 'maintenance']),
                name='bike_status_available',
            ),
        ]
        indexes = [
            models.Index(fields=['status']), 
            models.Index(fields=['bike_type']),
        ]
    def __str__(self):
        return f'{self.model} ({self.serial_number})'
    
    @property
    def is_available(self):
        return self.status == self.Status.AVAILABLE
    