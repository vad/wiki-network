from django import template
register = template.Library()

@register.filter
def unslugify(s):
    return s.replace('_', ' ').replace('-', ' ')
