from django.urls import path

from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.BikeListView.as_view(), name='bike_list'),
    path('add/', views.BikeCreateView.as_view(), name='bike_create'),
    path('<int:pk>/', views.BikeDetailView.as_view(), name='bike_detail'),
    path('<int:pk>/edit/', views.BikeUpdateView.as_view(), name='bike_edit'),
]
