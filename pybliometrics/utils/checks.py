"""Utility functions for parameter validation."""

def check_parameter_value(parameter: str, allowed: set[str], name: str) -> None:
    """Raise :class:`ValueError` if `parameter` is not allowed."""
    if parameter not in allowed:
        message = f"Parameter '{name}' must be one of {', '.join(allowed)}."
        raise ValueError(message)
