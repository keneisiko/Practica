from django import forms

from rentals.models import Rental

from .models import Bike


class BikeForm(forms.ModelForm):
    class Meta:
        model = Bike
        fields = ['model', 'serial_number', 'bike_type', 'status', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}
        error_messages = {
            'serial_number': {'unique': 'Велосипед с таким серийным номером уже есть.'},
        }

    def clean_serial_number(self):
        return self.cleaned_data['serial_number'].strip().upper()

    def clean_status(self):
        status = self.cleaned_data['status']
        has_active = (
            self.instance.pk is not None
            and Rental.objects.filter(bike=self.instance, status=Rental.Status.ACTIVE).exists()
        )
        if has_active and status != Bike.Status.RENTED:
            raise forms.ValidationError('У велосипеда есть активный прокат — сначала завершите его.')
        if not has_active and status == Bike.Status.RENTED:
            raise forms.ValidationError('Статус «В прокате» ставится автоматически при оформлении проката.')
        return status
