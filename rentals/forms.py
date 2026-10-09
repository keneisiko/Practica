from django import forms
from .models import Rental
from catalog.models import Bike

class RentalForm(forms.ModelForm):
    class Meta:
        model = Rental
        fields = ['client', 'bike', 'start_datetime', 'end_datetime']
        labels = {
            'client': 'Клиент',
            'bike': 'Велосипед',
            'start_datetime': 'Дата и время начала аренды',
            'end_datetime': 'Дата и время окончания аренды',
        }
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['bike'].queryset = Bike.objects.filter(status='available')
        if user and user.role == 'client':
            self.fields.pop('client')  # Убираем поле client для клиентов
    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_datetime')
        end = cleaned.get('end_datetime')
        bike = cleaned.get('bike')

        if start and end and end <= start:
            raise forms.ValidationError('Дата окончания аренды должна быть позже даты начала.')
        
        if bike and start and end:
            overlapping = Rental.objects.filter(
                bike=bike,
                status='active',
                start_datetime__lt=end,
                end_datetime__gt=start
            )
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                raise forms.ValidationError('Этот велосипед уже арендован в выбранный период.')