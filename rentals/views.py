from decimal import Decimal

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_naive, make_aware
from django.views import View
from django.views.decorators.http import require_GET
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.decorators import (
    AdminRequiredMixin,
    CanRentMixin,
    ManagerRequiredMixin,
    role_required,
)
from catalog.models import Bike
from pricing.services import DISCOUNT_RATE, DISCOUNT_THRESHOLD_DAYS, calculate_rental_cost, rental_days

from .forms import ClientForm, RentalAdminForm, RentalForm
from .models import Client, Rental
from .services import RentalError, cancel_rental, complete_rental, create_rental, update_rental


def visible_rentals(user):
    """Прокаты, которые пользователь имеет право видеть: менеджер — все, клиент — только свои."""
    qs = Rental.objects.select_related('client', 'bike', 'bike__bike_type', 'created_by')
    if user.is_manager_role:
        return qs
    return qs.filter(client__user=user)


# --- Прокаты ------------------------------------------------------------------------


class RentalCreateView(CanRentMixin, CreateView):
    model = Rental
    form_class = RentalForm
    template_name = 'rentals/rental_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        bike_id = self.request.GET.get('bike', '')
        if bike_id.isdigit():
            initial['bike'] = int(bike_id)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['discount_days'] = DISCOUNT_THRESHOLD_DAYS
        context['discount_percent'] = int(DISCOUNT_RATE * 100)
        if not self.request.user.is_manager_role:
            context['client_profile'] = Client.objects.filter(user=self.request.user).first()
        return context

    def form_valid(self, form):
        user = self.request.user
        if user.is_manager_role:
            client = form.cleaned_data['client']
        else:
            client = Client.objects.filter(user=user).first()
            if client is None:
                form.add_error(None, 'К вашему аккаунту не привязан профиль клиента. Обратитесь к менеджеру.')
                return self.form_invalid(form)
        try:
            rental = create_rental(
                client=client,
                bike=form.cleaned_data['bike'],
                start_datetime=form.cleaned_data['start_datetime'],
                end_datetime=form.cleaned_data['end_datetime'],
                created_by=user,
            )
        except RentalError as exc:
            form.add_error('bike', str(exc))
            return self.form_invalid(form)
        messages.success(self.request, f'Прокат №{rental.pk} оформлен. Стоимость — {rental.total_cost} ₽.')
        return redirect('rentals:rental_detail', pk=rental.pk)


class RentalListView(CanRentMixin, ListView):
    template_name = 'rentals/rental_list.html'
    context_object_name = 'rentals'
    paginate_by = 15

    def get_queryset(self):
        qs = visible_rentals(self.request.user)
        status = self.request.GET.get('status', '')
        if status in Rental.Status.values:
            qs = qs.filter(status=status)
        q = self.request.GET.get('q', '').strip()
        if q and self.request.user.is_manager_role:
            qs = qs.filter(
                Q(client__last_name__icontains=q)
                | Q(client__first_name__icontains=q)
                | Q(client__phone__icontains=q)
                | Q(bike__model__icontains=q)
                | Q(bike__serial_number__icontains=q)
            )
        return qs.order_by('-start_datetime')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mine = visible_rentals(self.request.user)
        context['statuses'] = Rental.Status.choices
        context['current_status'] = self.request.GET.get('status', '')
        context['q'] = self.request.GET.get('q', '').strip()
        context['counts'] = {
            'all': mine.count(),
            'active': mine.filter(status=Rental.Status.ACTIVE).count(),
            'completed': mine.filter(status=Rental.Status.COMPLETED).count(),
        }
        return context


class RentalDetailView(CanRentMixin, DetailView):
    template_name = 'rentals/rental_detail.html'
    context_object_name = 'rental'

    def get_queryset(self):
        # Чужой прокат для клиента просто «не существует» — 404, без подсказок.
        return visible_rentals(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rental = self.object
        days = rental_days(rental.start_datetime, rental.end_datetime)
        context['days'] = days
        context['base_cost'] = rental.bike.bike_type.base_price_per_day * days
        context['has_discount'] = days >= DISCOUNT_THRESHOLD_DAYS
        context['discount_percent'] = int(DISCOUNT_RATE * 100)
        return context


class RentalCompleteView(ManagerRequiredMixin, View):
    """Завершение проката: GET — подтверждение, POST — выполнение."""

    template_name = 'rentals/rental_confirm_complete.html'

    def get_rental(self, pk):
        return get_object_or_404(visible_rentals(self.request.user), pk=pk)

    def get(self, request, pk):
        return render(request, self.template_name, {'rental': self.get_rental(pk)})

    def post(self, request, pk):
        rental = self.get_rental(pk)
        try:
            complete_rental(rental)
        except RentalError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f'Прокат №{rental.pk} завершён, велосипед «{rental.bike.model}» снова доступен.')
        return redirect('rentals:rental_detail', pk=rental.pk)


class RentalCancelView(CanRentMixin, View):
    """Отмена проката: GET — подтверждение, POST — выполнение.

    Менеджер и администратор отменяют любой прокат, клиент — только свой
    (чужой прокат клиенту не виден, поэтому для него вернётся 404).
    """

    template_name = 'rentals/rental_confirm_cancel.html'

    def get_rental(self, pk):
        return get_object_or_404(visible_rentals(self.request.user), pk=pk)

    def get(self, request, pk):
        return render(request, self.template_name, {'rental': self.get_rental(pk)})

    def post(self, request, pk):
        rental = self.get_rental(pk)
        try:
            cancel_rental(rental)
        except RentalError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f'Прокат №{rental.pk} отменён, велосипед «{rental.bike.model}» снова доступен.')
        return redirect('rentals:rental_detail', pk=rental.pk)


class RentalUpdateView(AdminRequiredMixin, UpdateView):
    form_class = RentalAdminForm
    template_name = 'rentals/rental_admin_form.html'
    context_object_name = 'rental'

    def get_queryset(self):
        return visible_rentals(self.request.user)

    def form_valid(self, form):
        try:
            rental = update_rental(self.object, **{f: form.cleaned_data[f] for f in form.Meta.fields})
        except RentalError as exc:
            form.add_error('bike', str(exc))
            return self.form_invalid(form)
        messages.success(self.request, f'Прокат №{rental.pk} сохранён. Стоимость пересчитана: {rental.total_cost} ₽.')
        return redirect('rentals:rental_detail', pk=rental.pk)


@require_GET
@role_required(lambda user: user.can_rent)
def rental_estimate(request):
    """Предварительный расчёт стоимости для формы (JSON). Использует тот же сервис, что и сохранение."""

    def parse(name):
        value = parse_datetime(request.GET.get(name, ''))
        if value is not None and is_naive(value):
            value = make_aware(value)
        return value

    bike_id = request.GET.get('bike', '')
    start, end = parse('start'), parse('end')
    if not bike_id.isdigit() or start is None or end is None:
        return JsonResponse({'ok': False, 'error': 'Выберите велосипед и укажите даты.'})
    bike = Bike.objects.select_related('bike_type').filter(pk=bike_id).first()
    if bike is None:
        return JsonResponse({'ok': False, 'error': 'Велосипед не найден.'})
    days = rental_days(start, end)
    if days == 0:
        return JsonResponse({'ok': False, 'error': 'Окончание должно быть позже начала.'})
    price = bike.bike_type.base_price_per_day
    total = calculate_rental_cost(bike.bike_type, start, end)
    return JsonResponse({
        'ok': True,
        'days': days,
        'price_per_day': str(price),
        'base_cost': str((price * days).quantize(Decimal('0.01'))),
        'discount': days >= DISCOUNT_THRESHOLD_DAYS,
        'total': str(total),
    })


# --- Клиенты (администратор) --------------------------------------------------------


class ClientListView(AdminRequiredMixin, ListView):
    template_name = 'rentals/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20

    def get_queryset(self):
        qs = Client.objects.select_related('user').order_by('last_name', 'first_name')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(last_name__icontains=q) | Q(first_name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '').strip()
        return context


class ClientCreateView(AdminRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'rentals/client_form.html'
    success_url = reverse_lazy('rentals:client_list')

    def form_valid(self, form):
        messages.success(self.request, f'Клиент {form.instance.full_name} добавлен.')
        return super().form_valid(form)


class ClientUpdateView(AdminRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'rentals/client_form.html'

    def get_success_url(self):
        return reverse('rentals:client_list')

    def form_valid(self, form):
        messages.success(self.request, f'Данные клиента {form.instance.full_name} сохранены.')
        return super().form_valid(form)
