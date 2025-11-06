from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary"""
    return dictionary.get(key)

@register.filter
def to_int(value):
    """Convert a string or float to integer safely."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0
