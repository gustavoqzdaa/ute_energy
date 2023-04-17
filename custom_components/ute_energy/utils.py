"""Ute energy utils methods"""

import random
import string


def generate_random_agent_id() -> str:
    letters = "ABCDEFGH"
    result_str = "".join(random.choice(letters) for i in range(13))
    return result_str


def generate_random_string(length):
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str
