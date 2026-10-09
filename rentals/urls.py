from django.urls import path
from . import views

app_name = 'rentals'

urlpatterns = [
    path('create/', views.RentalCreateView.as_view(), name='rental_create'),
]