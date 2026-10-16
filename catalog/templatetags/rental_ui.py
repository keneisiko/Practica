from django import template

register = template.Library()

# Цветовая тема карточки по типу велосипеда (классы описаны в static/css/main.css).
TYPE_CLASSES = {
    'горный': 'type--mountain',
    'шоссейный': 'type--road',
    'городской': 'type--city',
    'детский': 'type--kids',
    'электровелосипед': 'type--electric',
}


@register.filter
def type_class(bike_type):
    name = getattr(bike_type, 'name', '') or ''
    return TYPE_CLASSES.get(name.strip().lower(), '')


@register.filter
def initials(user):
    letters = (user.first_name[:1] + user.last_name[:1]) if user.first_name else user.username[:2]
    return letters.upper()


@register.inclusion_tag('includes/field.html')
def form_field(field):
    """Поле формы с подписью, подсказкой и ошибками в едином стиле."""
    return {'field': field}
