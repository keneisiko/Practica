from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

admin.site.site_header = 'Прокат велосипедов — администрирование'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='catalog:bike_list', permanent=False)),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('catalog/', include('catalog.urls')),
    path('rentals/', include('rentals.urls')),
]
