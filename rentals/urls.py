from django.urls import path

from . import views

app_name = 'rentals'

urlpatterns = [
    path('', views.RentalListView.as_view(), name='rental_list'),
    path('create/', views.RentalCreateView.as_view(), name='rental_create'),
    path('estimate/', views.rental_estimate, name='rental_estimate'),
    path('<int:pk>/', views.RentalDetailView.as_view(), name='rental_detail'),
    path('<int:pk>/complete/', views.RentalCompleteView.as_view(), name='rental_complete'),
    path('<int:pk>/cancel/', views.RentalCancelView.as_view(), name='rental_cancel'),
    path('<int:pk>/edit/', views.RentalUpdateView.as_view(), name='rental_edit'),
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('clients/add/', views.ClientCreateView.as_view(), name='client_create'),
    path('clients/<int:pk>/edit/', views.ClientUpdateView.as_view(), name='client_edit'),
]
