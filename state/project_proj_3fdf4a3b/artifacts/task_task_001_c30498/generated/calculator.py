"""
Simple calculator module with basic arithmetic operations.
"""


def add(a: float, b: float) -> float:
    """
    Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b

    Examples:
        >>> add(2, 3)
        5
        >>> add(-1, 1)
        0
        >>> add(2.5, 3.5)
        6.0
    """
    return a + b


if __name__ == "__main__":
    # Simple demonstration
    print("Calculator Demo")
    print(f"2 + 3 = {add(2, 3)}")
    print(f"10.5 + 5.5 = {add(10.5, 5.5)}")
    print(f"-7 + 3 = {add(-7, 3)}")
