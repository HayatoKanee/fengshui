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
