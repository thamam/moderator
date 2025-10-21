#!/usr/bin/env python3
"""
greeter.py - A simple greeting application

This script prompts the user for their name and prints a personalized greeting.
"""


def main() -> None:
    """Main application logic for the greeter."""
    # Prompt user for their name
    name = input("Please enter your name: ")

    # Print personalized greeting
    print(f"Hello, {name}!")


if __name__ == "__main__":
    main()
