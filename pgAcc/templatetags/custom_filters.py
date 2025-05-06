from django import template

register = template.Library()

@register.filter
def star_rating(value):
    """
    Converts a numeric rating (1-5) to star symbols
    Example: 4 becomes ★★★★☆
    """
    try:
        value = int(value)
        full_stars = '★' * value
        empty_stars = '☆' * (5 - value)
        return full_stars + empty_stars
    except (ValueError, TypeError):
        return '☆☆☆☆☆'