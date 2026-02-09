"""
Custom template filters for number formatting.
Colombian format: $95.200,00 (dots for thousands, comma for decimals)
"""

from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter(name="colombian_currency")
def colombian_currency(value, decimals=2):
    """
    Format a number as Colombian currency.
    Example: 95200.00 -> $95.200,00

    Usage in templates:
        {{ value|colombian_currency }}
        {{ value|colombian_currency:0 }}  # No decimals
    """
    if value is None:
        return "$0,00"

    try:
        # Convert to Decimal for precise handling
        if isinstance(value, str):
            value = value.replace(",", ".")
        num = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return "$0,00"

    # Handle negative numbers
    is_negative = num < 0
    num = abs(num)

    # Round to specified decimals
    decimals = int(decimals)
    if decimals > 0:
        format_str = f"{{:.{decimals}f}}"
        formatted = format_str.format(float(num))
    else:
        formatted = str(int(round(float(num))))

    # Split integer and decimal parts
    if "." in formatted:
        integer_part, decimal_part = formatted.split(".")
    else:
        integer_part = formatted
        decimal_part = "00" if decimals > 0 else ""

    # Add thousand separators (dots)
    integer_with_dots = ""
    for i, digit in enumerate(reversed(integer_part)):
        if i > 0 and i % 3 == 0:
            integer_with_dots = "." + integer_with_dots
        integer_with_dots = digit + integer_with_dots

    # Build final string
    if decimals > 0:
        result = f"{integer_with_dots},{decimal_part}"
    else:
        result = integer_with_dots

    if is_negative:
        return f"-${result}"
    return f"${result}"


@register.filter(name="colombian_number")
def colombian_number(value, decimals=2):
    """
    Format a number in Colombian style without currency symbol.
    Example: 95200.00 -> 95.200,00

    Usage in templates:
        {{ value|colombian_number }}
        {{ value|colombian_number:1 }}  # One decimal
    """
    if value is None:
        return "0,00"

    try:
        if isinstance(value, str):
            value = value.replace(",", ".")
        num = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return "0,00"

    is_negative = num < 0
    num = abs(num)

    decimals = int(decimals)
    if decimals > 0:
        format_str = f"{{:.{decimals}f}}"
        formatted = format_str.format(float(num))
    else:
        formatted = str(int(round(float(num))))

    if "." in formatted:
        integer_part, decimal_part = formatted.split(".")
    else:
        integer_part = formatted
        decimal_part = "00" if decimals > 0 else ""

    # Add thousand separators
    integer_with_dots = ""
    for i, digit in enumerate(reversed(integer_part)):
        if i > 0 and i % 3 == 0:
            integer_with_dots = "." + integer_with_dots
        integer_with_dots = digit + integer_with_dots

    if decimals > 0:
        result = f"{integer_with_dots},{decimal_part}"
    else:
        result = integer_with_dots

    if is_negative:
        return f"-{result}"
    return result


@register.filter(name="colombian_percent")
def colombian_percent(value, decimals=1):
    """
    Format a percentage in Colombian style.
    Example: 25.5 -> 25,5%

    Usage in templates:
        {{ value|colombian_percent }}
        {{ value|colombian_percent:0 }}  # No decimals
    """
    if value is None:
        return "0%"

    try:
        num = float(value)
    except (ValueError, TypeError):
        return "0%"

    is_negative = num < 0
    num = abs(num)

    decimals = int(decimals)
    if decimals > 0:
        format_str = f"{{:.{decimals}f}}"
        formatted = format_str.format(num)
        # Replace dot with comma for decimals
        formatted = formatted.replace(".", ",")
    else:
        formatted = str(int(round(num)))

    if is_negative:
        return f"-{formatted}%"
    return f"{formatted}%"
