from uuid import UUID
from argparse import ArgumentTypeError


def uuid(param):
    try:
        return str(UUID(param))
    except Exception:
        raise ArgumentTypeError("Not a valid UUID!")


def is_primer(value):
    if isinstance(value, str) and not value.isalpha():
        raise ArgumentTypeError("Only letters are allowed")
    return value.upper() if isinstance(value, str) else value
