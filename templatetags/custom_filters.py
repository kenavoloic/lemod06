from django import template
from django.utils import timezone, translation

register = template.Library()

# @register.filter
# def format_date_calendaire(envoi):
#     if envoi is None:
#         envoi = timezone.now()
#         date_formatee = envoi.strftime("%A %d %B %Y")
#         date_formatee = date_formatee[0].upper() + date_formatee[1:]
#         return date_formatee

# @register.simple_tag  # Utilisez simple_tag au lieu de filter, car il n'y a pas de paramètre d'entrée
# def date_actuelle_formatee():
#     with translation.override('fr'):
#         date_actuelle = timezone.now()
#         date_formatee = date_actuelle.strftime("%A %d %B %Y")
#         date_formatee = date_formatee.capitalize()
#         return date_formatee
    
@register.simple_tag
def date_actuelle_formatee():
    envoi = timezone.now()
    date_formatee = envoi.strftime("%A %d %B %Y")
    date_formatee = date_formatee[0].upper() + date_formatee[1:]
    return date_formatee
