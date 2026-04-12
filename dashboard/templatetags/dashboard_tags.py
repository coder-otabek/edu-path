"""dashboard/templatetags/dashboard_tags.py"""
import json
from django import template

register = template.Library()

@register.filter
def parse_json(value):
    """JSON string ni Python listga aylantiradi"""
    if not value:
        return []
    try:
        result = json.loads(value)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []

@register.filter
def enumerate(value):
    """List ni enumerate qiladi"""
    return list(__builtins__['enumerate'](value)) if value else []