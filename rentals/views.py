from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from accounts.decorators import RoleRequiredMixin
from pricing.services import calculate_rental_cost
from catalog.models import Bike
from .models import Rental
from .forms import RentalForm


class RentalCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ['client', 'manager', 'admin']
    model = Rental
    form_class = RentalForm
    template_name = 'rentals/rental_form.html'
    success_url = reverse_lazy('catalog:bike_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        bike_id = self.request.GET.get('bike')
        if bike_id:
            try:
                initial['bike'] = int(bike_id)
            except (ValueError, TypeError):
                pass
        return initial

    @transaction.atomic
    def form_valid(self, form):
        rental = form.save(commit=False)

        if self.request.user.role == 'client':
            rental.client = self.request.user.client_profile

        rental.created_by = self.request.user
        rental.total_cost = calculate_rental_cost(
            rental.bike.bike_type,
            rental.start_datetime,
            rental.end_datetime,
        )
        rental.save()

        rental.bike.status = Bike.Status.RENTED
        rental.bike.save()

        messages.success(self.request, 'Прокат успешно оформлен.')
        return super().form_valid(form)