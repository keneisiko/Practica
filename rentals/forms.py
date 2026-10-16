import re

from django import forms

from catalog.models import Bike

from .models import Client, Rental

DATETIME_FORMAT = '%Y-%m-%dT%H:%M'  # формат <input type="datetime-local">
PHONE_RE = re.compile(r'^\+?\d{10,15}$')


def datetime_widget():
    return forms.DateTimeInput(attrs={'type': 'datetime-local'}, format=DATETIME_FORMAT)


class BikeChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, bike):
        return f'{bike.model} · {bike.bike_type.name} · {bike.bike_type.base_price_per_day:.0f} ₽/сутки'


class ClientChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, client):
        return f'{client.full_name} · {client.phone}'


class RentalPeriodMixin:
    """Общие проверки дат и пересечения прокатов для форм оформления и редактирования."""

    def clean_period(self, cleaned, bike):
        start = cleaned.get('start_datetime')
        end = cleaned.get('end_datetime')
        if start and end and end <= start:
            self.add_error('end_datetime', 'Дата и время окончания должны быть позже начала проката.')
            return
        if bike and start and end:
            overlapping = Rental.objects.filter(
                bike=bike,
                status=Rental.Status.ACTIVE,
                start_datetime__lt=end,
                end_datetime__gt=start,
            )
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                self.add_error('bike', 'Этот велосипед уже арендован на выбранный период.')


class RentalForm(RentalPeriodMixin, forms.ModelForm):
    """Оформление проката. Клиент оформляет на себя (поля «Клиент» нет), менеджер — на любого клиента."""

    client = ClientChoiceField(
        queryset=Client.objects.order_by('last_name', 'first_name'),
        label='Клиент',
        empty_label='— выберите клиента —',
        error_messages={'required': 'Выберите клиента.', 'invalid_choice': 'Такого клиента нет.'},
    )
    bike = BikeChoiceField(
        queryset=Bike.objects.none(),
        label='Велосипед',
        empty_label='— выберите велосипед —',
        error_messages={
            'required': 'Выберите велосипед.',
            'invalid_choice': 'Этот велосипед недоступен для проката — выберите другой.',
        },
    )

    class Meta:
        model = Rental
        fields = ['client', 'bike', 'start_datetime', 'end_datetime']
        widgets = {
            'start_datetime': datetime_widget(),
            'end_datetime': datetime_widget(),
        }
        error_messages = {
            'start_datetime': {'required': 'Укажите дату и время начала.'},
            'end_datetime': {'required': 'Укажите дату и время окончания.'},
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Выбрать можно только доступный велосипед — и в списке, и при подделке запроса.
        self.fields['bike'].queryset = (
            Bike.objects.filter(status=Bike.Status.AVAILABLE).select_related('bike_type').order_by('model')
        )
        if user is not None and not user.is_manager_role:
            del self.fields['client']

    def clean(self):
        cleaned = super().clean()
        self.clean_period(cleaned, cleaned.get('bike'))
        return cleaned


class RentalAdminForm(RentalPeriodMixin, forms.ModelForm):
    """Редактирование проката администратором. Стоимость пересчитывается автоматически."""

    client = ClientChoiceField(queryset=Client.objects.order_by('last_name', 'first_name'), label='Клиент')
    bike = BikeChoiceField(queryset=Bike.objects.select_related('bike_type').order_by('model'), label='Велосипед')

    class Meta:
        model = Rental
        fields = ['client', 'bike', 'start_datetime', 'end_datetime', 'status']
        widgets = {
            'start_datetime': datetime_widget(),
            'end_datetime': datetime_widget(),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('status') == Rental.Status.ACTIVE:
            self.clean_period(cleaned, cleaned.get('bike'))
        else:
            start, end = cleaned.get('start_datetime'), cleaned.get('end_datetime')
            if start and end and end <= start:
                self.add_error('end_datetime', 'Дата и время окончания должны быть позже начала проката.')
        return cleaned


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['last_name', 'first_name', 'phone', 'email']
        widgets = {
            'phone': forms.TextInput(attrs={'type': 'tel', 'placeholder': '+79000000000'}),
        }
        error_messages = {
            'phone': {'unique': 'Клиент с таким телефоном уже есть.'},
            'email': {'unique': 'Клиент с таким email уже есть.'},
        }

    def clean_phone(self):
        phone = re.sub(r'[\s()-]', '', self.cleaned_data['phone'])
        if not PHONE_RE.match(phone):
            raise forms.ValidationError('Телефон: от 10 до 15 цифр, можно с «+» в начале.')
        return phone

    def clean_email(self):
        return self.cleaned_data.get('email') or None
