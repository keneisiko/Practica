from .forms import RegisterForm
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.contrib import messages
from django.db import transaction
from .models import User
from rentals.models import Client

# Create your views here.

class RegisterView(FormView):
    form_class = RegisterForm 
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('catalog:bike_list')

    @transaction.atomic
    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password1']
        email = form.cleaned_data.get('email') or None

        user = User.objects.create_user(
            username = username,
            password = password,
            email = email,
            role=User.Role.CLIENT,
        )
        client = Client.objects.create(
            last_name=form.cleaned_data['last_name'],
            first_name=form.cleaned_data['first_name'],
            email=email,
            phone=form.cleaned_data['phone'],
            user=user,
        )
        login(self.request, user)
        messages.success(self.request, 'Регистрация прошла успешно')
        return super().form_valid(form)
        
        
