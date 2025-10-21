#!/usr/bin/env python3
"""
Greeter Script

A simple interactive script that asks for a user's name and prints a greeting.

Usage:
    python greeter.py

The script will prompt for a name and display a personalized greeting.
"""


def get_name() -> str:
    """
    Prompt the user to enter their name.

    Returns:
        str: The name entered by the user (stripped of leading/trailing whitespace).

    Note:
        Returns an empty string if user enters nothing.
    """
    name = input("What is your name? ")
    return name.strip()


def greet(name: str) -> str:
    """
    Generate a greeting message for the given name.

    Args:
        name (str): The name to include in the greeting.

    Returns:
        str: A formatted greeting message.

    Examples:
        >>> greet("Alice")
        'Hello, Alice!'
        >>> greet("Bob")
        'Hello, Bob!'
    """
    return f"Hello, {name}!"


def main() -> None:
    """
    Main entry point for the greeter script.

    Prompts the user for their name and prints a greeting.
    If no name is provided, prints a generic greeting.
    """
    name = get_name()

    if name:
        greeting = greet(name)
        print(greeting)
    else:
        print("Hello, there!")


if __name__ == "__main__":
    main()
