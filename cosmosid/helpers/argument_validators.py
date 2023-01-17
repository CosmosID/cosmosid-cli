from uuid import UUID
from argparse import ArgumentTypeError


def uuid(param):
    try:
        return str(UUID(param))
    except Exception:
        raise ArgumentTypeError("Not a valid UUID!")
