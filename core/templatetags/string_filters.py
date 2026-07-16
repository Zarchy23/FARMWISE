from django import template

register = template.Library()


@register.filter
def replace(value, args):
    """
    Replace all occurrences of a string with another string.
    Usage: {{ value|replace:"old:new" }}
    """
    if ':' not in args:
        return value
    
    old, new = args.split(':', 1)
    return str(value).replace(old, new)


@register.filter
def replace_underscore(value):
    """Replace underscores with spaces."""
    return str(value).replace('_', ' ')
