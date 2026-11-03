from decimal import Decimal, InvalidOperation

from app.errors import ValidationError


def clean_text(value):
    return str(value or "").strip()


def as_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def parse_decimal(value, label, minimum=None, maximum=None):
    text = clean_text(value).replace(" ", "").replace(",", ".")
    if not text:
        raise ValidationError(f"Въведете {label}.")
    try:
        number = Decimal(text)
    except InvalidOperation:
        raise ValidationError(f"{label} трябва да е число.") from None
    if minimum is not None and number < minimum:
        raise ValidationError(f"{label} трябва да е поне {minimum}.")
    if maximum is not None and number > maximum:
        raise ValidationError(f"{label} трябва да е най-много {maximum}.")
    return number.quantize(Decimal("0.01"))


def parse_int(value, label, minimum=None, maximum=None, required=True):
    text = clean_text(value)
    if not text:
        if required:
            raise ValidationError(f"Въведете {label}.")
        return None
    try:
        number = int(text)
    except ValueError:
        raise ValidationError(f"{label} трябва да е цяло число.") from None
    if minimum is not None and number < minimum:
        raise ValidationError(f"{label} трябва да е поне {minimum}.")
    if maximum is not None and number > maximum:
        raise ValidationError(f"{label} трябва да е най-много {maximum}.")
    return number


def optional_decimal(value):
    text = clean_text(value).replace(" ", "").replace(",", ".")
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None
