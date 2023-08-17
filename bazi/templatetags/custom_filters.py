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
