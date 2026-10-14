import math


def check_numeric_answer(
    user_value: float,
    expected_value: float,
    tolerance: float,
) -> bool:
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    return math.isfinite(user_value) and abs(user_value - expected_value) <= tolerance
