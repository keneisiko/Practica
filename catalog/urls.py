from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.BikeListView.as_view(), name='bike_list'),
    path('<int:pk>/', views.BikeDetailView.as_view(), name='bike_detail'),
]