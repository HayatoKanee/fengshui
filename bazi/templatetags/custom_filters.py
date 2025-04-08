from django import template

from bazi.feixing import mountains_24

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


@register.simple_tag
def get_direction_grid(star):
    """
    Given a star (a string from the 24-mountain circle), returns a dictionary
    with eight direction values computed from the standard 24-mountain list.

    The list is assumed to be ordered as follows:

         0: 子,  1: 癸,  2: 丑,  3: 艮,  4: 寅,  5: 甲,  6: 卯,  7: 乙,
         8: 辰,  9: 巽, 10: 巳, 11: 丙, 12: 午, 13: 丁, 14: 未, 15: 坤,
        16: 申, 17: 庚, 18: 酉, 19: 辛, 20: 戌, 21: 乾, 22: 亥, 23: 壬

    The mapping for a 3×3 directional grid (outer cells only) is:
      - Bottom (center of bottom row): star (i)
      - Bottom-right: (i + 3) mod 24
      - Right (center of right column): (i + 6) mod 24
      - Top-right: (i + 9) mod 24
      - Top (center of top row): (i + 12) mod 24
      - Top-left: (i + 15) mod 24
      - Left (center of left column): (i + 18) mod 24
      - Bottom-left: (i + 21) mod 24
    """

    if not star:
         return {
        "bottom": "",
        "right": "",
        "top": "",
        "left": "",
    }
    i = mountains_24.index(star)

    return {
        "bottom": mountains_24[i % 24],
        "right": mountains_24[(i + 6) % 24],
        "top": mountains_24[(i + 12) % 24],
        "left": mountains_24[(i + 18) % 24],
    }
