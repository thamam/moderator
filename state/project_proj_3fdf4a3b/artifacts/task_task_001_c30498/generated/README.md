# Calculator

A simple Python calculator module with basic arithmetic operations.

## Features

- `add(a, b)`: Add two numbers together

## Requirements

- Python 3.9 or higher
- No external dependencies required

## Installation

No installation needed. Simply clone or download the `calculator.py` file.

## Usage

### As a Module

```python
from calculator import add

result = add(5, 3)
print(result)  # Output: 8
```

### Running Directly

```bash
python calculator.py
```

This will run a simple demonstration of the add function.

## Examples

```python
from calculator import add

# Integer addition
print(add(2, 3))      # 5

# Floating point addition
print(add(2.5, 3.5))  # 6.0

# Negative numbers
print(add(-7, 3))     # -4

# Mixed types
print(add(10, 5.5))   # 15.5
```

## Testing

The function includes docstring examples that can be tested with Python's doctest:

```bash
python -m doctest calculator.py -v
```

## Future Enhancements

- Add subtract, multiply, and divide functions
- Add error handling for division by zero
- Add support for more complex operations
- Add comprehensive unit tests
