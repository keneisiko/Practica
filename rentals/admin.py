from django.contrib import admin
from .models import Client, Rental

# Register your models here.

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'user')  # Поля, которые будут отображаться в списке клиентов
    search_fields = ('first_name', 'last_name', 'email', 'phone')  # Поля, по которым можно искать клиентов
    ordering = ('last_name', 'first_name')  # Порядок сортировки по фамилии
    autocomplete_fields = ('user',)  # Поля, для которых будет включено автозаполнение
    readonly_fields = ('created_at',)  # Поля, которые будут доступны только для чтения

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'bike', 'start_datetime', 'end_datetime', 'total_cost', 'status')  # Поля, которые будут отображаться в списке аренд
    list_filter = ('status', 'start_datetime',)  # Фильтры по статусу и датам
    search_fields = ('client__first_name', 'client__last_name', 'bike__name', 'bike__serial_number')  # Поля, по которым можно искать аренды
    date_hierarchy = 'start_datetime'  # Иерархия по дате начала аренды
    autocomplete_fields = ('client', 'bike', 'created_by')  # Поля, для которых будет включено автозаполнение
    readonly_fields = ('created_at',)  # Поля, которые будут доступны только для чтения
    ordering = ('-start_datetime',)  # Порядок сортировки по дате начала аренды (по убыванию)
