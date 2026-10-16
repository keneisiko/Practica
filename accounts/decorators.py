from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

FORBIDDEN_MESSAGE = 'У вашей роли нет доступа к этой функции.'


def _check_access(request, test, message):
    """Аноним — на страницу входа (с ?next=), вошедший без прав — 403 с понятным сообщением."""
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    if not test(request.user):
        raise PermissionDenied(message)
    return None


def role_required(test, message=FORBIDDEN_MESSAGE):
    """Декоратор для функций-вьюх: @role_required(lambda user: user.is_manager_role)."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            denied = _check_access(request, test, message)
            if denied is not None:
                return denied
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


class RoleRequiredMixin:
    """Миксин для CBV. Ставится в списке базовых классов ПЕРЕД generic-вьюхой.

    Переопредели `has_role_access(user)` или используй готовые миксины ниже.
    """

    permission_message = FORBIDDEN_MESSAGE

    def has_role_access(self, user):
        return True

    def dispatch(self, request, *args, **kwargs):
        denied = _check_access(request, self.has_role_access, self.permission_message)
        if denied is not None:
            return denied
        return super().dispatch(request, *args, **kwargs)


class CanRentMixin(RoleRequiredMixin):
    permission_message = 'Оформлять прокат могут только клиенты, менеджеры и администраторы.'

    def has_role_access(self, user):
        return user.can_rent


class ManagerRequiredMixin(RoleRequiredMixin):
    permission_message = 'Эта функция доступна только менеджерам и администраторам.'

    def has_role_access(self, user):
        return user.is_manager_role


class AdminRequiredMixin(RoleRequiredMixin):
    permission_message = 'Эта функция доступна только администратору.'

    def has_role_access(self, user):
        return user.is_admin_role
