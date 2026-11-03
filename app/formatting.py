from datetime import datetime
from decimal import Decimal


def format_price(value, decimals=False):
    if value is None or value == "":
        return "—"
    number = Decimal(str(value)).quantize(Decimal("0.01"))
    if not decimals and number == number.to_integral():
        text = f"{int(number):,}".replace(",", " ")
        return f"{text} €"
    text = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", " ")
    return f"{text} €"


def format_ppm(value):
    if value is None or value == "":
        return "—"
    return format_price(value, decimals=True).replace(" €", " €/m²")


def format_sqm(value):
    if value is None or value == "":
        return "—"
    number = Decimal(str(value)).quantize(Decimal("0.01"))
    if number == number.to_integral():
        text = f"{int(number):,}".replace(",", " ")
    else:
        text = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", " ")
    return f"{text} м²"


def format_when(value):
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y %H:%M")
    return value or ""
