"""Ute energy utils methods"""

import random
import string
import re
import calendar


def generate_random_agent_id() -> str:
    """Generate random agent"""
    letters = "ABCDEFGH"
    result_str = "".join(random.choice(letters) for i in range(13))
    return result_str


def generate_random_string(length: int):
    """Generate random string"""
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str


def convert_to_snake_case(name: str) -> str:
    """Convert string to snake_case"""
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    name = re.sub("__([A-Z])", r"_\1", name)
    name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower()


def convert_number_to_month(month: int) -> str:
    """Convert a number to month"""
    return calendar.month_abbr[month]
