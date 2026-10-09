from django.db.models import Q
from django.views.generic import ListView
from catalog.models import Bike, BikeType
from django.views.generic import DetailView

# Create your views here.

class BikeListView(ListView):
    model = Bike
    template_name = 'catalog/bike_list.html'
    context_object_name = 'bikes'
    paginate_by = 12

    def get_queryset(self):
        qs = Bike.objects.select_related('bike_type')
        q = self.request.GET.get('q','').strip()
        bike_type = self.request.GET.get('bike_type','')
        status = self.request.GET.get('status','')
        sort = self.request.GET.get('sort','model')
        if q:
            qs = qs.filter(Q(model__icontains=q) | Q(serial_number__icontains=q))
        if bike_type:
            qs = qs.filter(bike_type_id=bike_type)
        if status:
            qs = qs.filter(status=status)
        allowed_sorts = ['model', '-model', 'bike_type__base_price_per_day', '-bike_type__base_price_per_day']
        if sort in allowed_sorts:
            qs = qs.order_by(sort)
        else:
            qs = qs.order_by('model')
        return qs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bike_types'] = BikeType.objects.all()
        context['current_filters'] = {
            'q': self.request.GET.get('q', '').strip(),
            'bike_type': self.request.GET.get('bike_type', ''),
            'status': self.request.GET.get('status', ''),
            'sort': self.request.GET.get('sort', 'model'),
        }
        return context
class BikeDetailView(DetailView):
    model = Bike
    template_name = 'catalog/bike_detail.html'
    context_object_name = 'bike'
