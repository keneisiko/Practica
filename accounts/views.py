from django.contrib import messages
from django.contrib.auth import login
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from rentals.models import Client

from .forms import RegisterForm
from .models import User


class RegisterView(FormView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('catalog:bike_list')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('catalog:bike_list')
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        email = form.cleaned_data.get('email')
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1'],
            email=email or '',
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            role=User.Role.CLIENT,
        )
        Client.objects.create(
            user=user,
            last_name=form.cleaned_data['last_name'],
            first_name=form.cleaned_data['first_name'],
            phone=form.cleaned_data['phone'],
            email=email,
        )
        login(self.request, user)
        messages.success(self.request, f'Добро пожаловать, {user.first_name}! Регистрация прошла успешно.')
        return redirect(self.get_success_url())
