from django.contrib import messages
from django.db.models import Count, Q
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.decorators import AdminRequiredMixin

from .forms import BikeForm
from .models import Bike, BikeType

ALLOWED_SORTS = {
    'model': 'Модель (А–Я)',
    '-model': 'Модель (Я–А)',
    'bike_type__base_price_per_day': 'Сначала дешёвые',
    '-bike_type__base_price_per_day': 'Сначала дорогие',
}


def can_search(user):
    return user.is_authenticated and user.can_search_catalog


class BikeListView(ListView):
    """Каталог. Посетитель видит список, поиск/фильтры/сортировка — для клиентов и сотрудников."""

    model = Bike
    template_name = 'catalog/bike_list.html'
    context_object_name = 'bikes'
    paginate_by = 12

    def get_filters(self):
        if not can_search(self.request.user):
            return {'q': '', 'bike_type': '', 'status': '', 'sort': 'model'}
        get = self.request.GET
        sort = get.get('sort', 'model')
        return {
            'q': get.get('q', '').strip(),
            'bike_type': get.get('bike_type', '') if get.get('bike_type', '').isdigit() else '',
            'status': get.get('status', '') if get.get('status', '') in Bike.Status.values else '',
            'sort': sort if sort in ALLOWED_SORTS else 'model',
        }

    def get_queryset(self):
        filters = self.get_filters()
        qs = Bike.objects.select_related('bike_type')
        if filters['q']:
            qs = qs.filter(Q(model__icontains=filters['q']) | Q(serial_number__icontains=filters['q']))
        if filters['bike_type']:
            qs = qs.filter(bike_type_id=filters['bike_type'])
        if filters['status']:
            qs = qs.filter(status=filters['status'])
        return qs.order_by(filters['sort'], 'model')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filters = self.get_filters()
        context['current_filters'] = filters
        context['has_filters'] = any(filters[k] for k in ('q', 'bike_type', 'status')) or filters['sort'] != 'model'
        context['can_search'] = can_search(self.request.user)
        context['bike_types'] = BikeType.objects.annotate(
            available=Count('bikes', filter=Q(bikes__status=Bike.Status.AVAILABLE))
        )
        context['statuses'] = Bike.Status.choices
        context['sorts'] = ALLOWED_SORTS
        context['available_total'] = Bike.objects.filter(status=Bike.Status.AVAILABLE).count()
        context['bikes_total'] = Bike.objects.count()
        return context


class BikeDetailView(DetailView):
    model = Bike
    template_name = 'catalog/bike_detail.html'
    context_object_name = 'bike'

    def get_queryset(self):
        return Bike.objects.select_related('bike_type')


class BikeCreateView(AdminRequiredMixin, CreateView):
    model = Bike
    form_class = BikeForm
    template_name = 'catalog/bike_form.html'

    def get_success_url(self):
        return reverse('catalog:bike_detail', args=[self.object.pk])

    def form_valid(self, form):
        messages.success(self.request, f'Велосипед «{form.instance.model}» добавлен в каталог.')
        return super().form_valid(form)


class BikeUpdateView(AdminRequiredMixin, UpdateView):
    model = Bike
    form_class = BikeForm
    template_name = 'catalog/bike_form.html'

    def get_success_url(self):
        return reverse('catalog:bike_detail', args=[self.object.pk])

    def form_valid(self, form):
        messages.success(self.request, f'Изменения велосипеда «{form.instance.model}» сохранены.')
        return super().form_valid(form)
