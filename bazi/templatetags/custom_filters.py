from django import template

register = template.Library()


@register.filter(name='lookup')
def lookup(value, arg):
    return value.get(arg, '')


@register.filter
def keys_to_list(dictionary):
    return list(dictionary.keys())


@register.filter
def multiply(value, arg):
    return value * arg


@register.filter
def first_value(dictionary):
    return next(iter(dictionary.values()))


@register.filter
def get_item(lst, i):
    try:
        return lst[i]
    except:
        return ''

@register.filter(name='zip')
def zip_lists(a, b):
    """
    Zips together two lists so you can iterate over pairs in the template.
    """
    try:
        return zip(a, b)
    except Exception:
        return []

@register.filter
def to_range(value):
    """
    Returns a range of integers from 0 up to 'value' (exclusive).
    For example, 3|to_range ==> range(0,3) ==> [0,1,2].
    """
    return range(value)

@register.filter
def index(array_or_list, idx):
    """
    Returns array_or_list[idx].
    """
    try:
        return array_or_list[idx]
    except (IndexError, TypeError):
        return None
