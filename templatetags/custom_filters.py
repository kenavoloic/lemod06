from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def format_date_calendaire(envoi):
    if envoi is None:
        envoi = timezone.now()
        date_formatee = envoi.strftime("%A %d %B %Y")
        date_formatee = date_formatee[0].upper() + date_formatee[1:]
        return date_formatee
