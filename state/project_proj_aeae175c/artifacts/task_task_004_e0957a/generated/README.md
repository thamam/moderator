# Greeter Script

A simple, interactive Python script that asks for a user's name and prints a personalized greeting.

## Features

- Interactive command-line interface
- Input validation and whitespace trimming
- Graceful handling of empty input
- Support for Unicode characters and special names
- Comprehensive test coverage
- Type hints for better code clarity

## Requirements

- Python 3.6 or higher

## Installation

No installation required! Simply download the `greeter.py` file.

```bash
# Make the script executable (optional)
chmod +x greeter.py
```

## Usage

### Basic Usage

Run the script directly:

```bash
python greeter.py
```

Or, if you made it executable:

```bash
./greeter.py
```

### Example Session

```
$ python greeter.py
What is your name? Alice
Hello, Alice!
```

### Empty Input

If you don't enter a name, the script provides a generic greeting:

```
$ python greeter.py
What is your name?
Hello, there!
```

## Code Structure

The script is organized into three main functions:

### `get_name() -> str`
Prompts the user for their name and returns it (with whitespace trimmed).

### `greet(name: str) -> str`
Generates a greeting message for the given name.

### `main() -> None`
Main entry point that coordinates the name input and greeting display.

## Testing

A comprehensive test suite is provided in `test_greeter.py`.

### Running Tests

Run all tests:

```bash
python -m unittest test_greeter.py
```

Run tests with verbose output:

```bash
python -m unittest test_greeter.py -v
```

Run a specific test class:

```bash
python -m unittest test_greeter.TestGreet
```

### Test Coverage

The test suite includes 20+ tests covering:

- **Normal input handling**: Standard names
- **Whitespace handling**: Leading/trailing spaces, whitespace-only input
- **Empty input**: Graceful fallback behavior
- **Special characters**: Unicode, accents, hyphens, apostrophes
- **Edge cases**: Very long names, numeric strings, symbols
- **Integration tests**: End-to-end main() function behavior

### Test Organization

Tests are organized into four classes:

1. **TestGetName**: Tests for the `get_name()` function
2. **TestGreet**: Tests for the `greet()` function
3. **TestMain**: Integration tests for the `main()` function
4. **TestEdgeCases**: Boundary conditions and edge cases

## API Documentation

### Functions

#### `get_name()`
```python
def get_name() -> str
```

Prompts the user to enter their name via standard input.

**Returns:**
- `str`: The name entered by the user (with whitespace stripped)

**Example:**
```python
name = get_name()  # User enters "Alice"
# Returns: "Alice"
```

---

#### `greet(name)`
```python
def greet(name: str) -> str
```

Generates a greeting message for the given name.

**Parameters:**
- `name` (str): The name to include in the greeting

**Returns:**
- `str`: A formatted greeting message in the form "Hello, {name}!"

**Examples:**
```python
greet("Alice")     # Returns: "Hello, Alice!"
greet("Bob")       # Returns: "Hello, Bob!"
greet("María")     # Returns: "Hello, María!"
```

---

#### `main()`
```python
def main() -> None
```

Main entry point for the script. Prompts the user for their name and prints a greeting.

**Behavior:**
- If a name is provided: prints "Hello, {name}!"
- If no name is provided: prints "Hello, there!"

## Examples

### Using as a Module

You can also import and use the functions in your own code:

```python
from greeter import greet

# Generate greetings programmatically
message = greet("Alice")
print(message)  # Output: Hello, Alice!

# Use with a list of names
names = ["Alice", "Bob", "Charlie"]
for name in names:
    print(greet(name))
```

### Custom Integration

```python
from greeter import get_name, greet

def custom_greeter():
    """Custom greeting with additional formatting."""
    name = get_name()
    if name:
        greeting = greet(name)
        print(f"{'=' * len(greeting)}")
        print(greeting)
        print(f"{'=' * len(greeting)}")
    else:
        print("No name provided.")

custom_greeter()
```

## Edge Cases Handled

- **Empty input**: Displays "Hello, there!"
- **Whitespace-only input**: Treated as empty
- **Leading/trailing whitespace**: Automatically trimmed
- **Special characters**: Full Unicode support (accents, non-Latin scripts, etc.)
- **Very long names**: No length restrictions

## Development

### Code Style

The code follows Python best practices:
- PEP 8 style guidelines
- Type hints for function signatures
- Comprehensive docstrings
- Clear variable names

### Contributing

To contribute improvements:

1. Write tests for new functionality
2. Ensure all existing tests pass
3. Follow the existing code style
4. Add docstrings for new functions

## License

This is a simple educational script provided as-is for learning purposes.

## Troubleshooting

### Issue: Script doesn't run

**Solution:** Ensure you're using Python 3.6 or higher:
```bash
python --version
```

### Issue: Tests fail with import errors

**Solution:** Run tests from the same directory as `greeter.py`:
```bash
cd /path/to/greeter
python -m unittest test_greeter.py
```

### Issue: Permission denied when running `./greeter.py`

**Solution:** Make the script executable:
```bash
chmod +x greeter.py
```

## Future Enhancements

Potential improvements for future versions:

- Support for multiple languages
- Configurable greeting formats
- Time-based greetings (morning/afternoon/evening)
- Name validation (alphabetic characters only)
- Persistent greeting history
- GUI version using tkinter

## Version History

- **v1.0.0** (2024): Initial release
  - Basic name input and greeting
  - Comprehensive test suite
  - Full documentation
