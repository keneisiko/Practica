from django.contrib import admin
from .models import BikeType, Bike
# Register your models here.

@admin.register(BikeType)
class BikeTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price_per_day')  # Поля, которые будут отображаться в списке типов велосипедов
    search_fields = ('name',)  # Поля, по которым можно искать типы велосипедов
    ordering = ('name',)  # Порядок сортировки по имени

@admin.register(Bike)
class BikeAdmin(admin.ModelAdmin):
    list_display = ('model', 'serial_number', 'bike_type', 'status')  # Поля, которые будут отображаться в списке велосипедов
    list_filter = ('bike_type', 'status')  # Фильтры для списка велосипедов
    search_fields = ('model', 'serial_number')  # Поля, по которым можно искать велосипеды
    ordering = ('model',)  # Порядок сортировки по модели
    readonly_fields = ('created_at', 'updated_at')  # Поля created_at и updated_at будут доступны только для чтения