#!/usr/bin/env python3
"""
Test Suite for Greeter Script

Comprehensive tests covering all functionality in greeter.py including:
- Name input handling
- Greeting generation
- Edge cases (empty input, whitespace, special characters)
- Main function integration
"""

import unittest
from unittest.mock import patch
from io import StringIO
import greeter


class TestGetName(unittest.TestCase):
    """Test cases for the get_name() function."""

    @patch('builtins.input', return_value='Alice')
    def test_get_name_normal_input(self, mock_input):
        """Test get_name with normal name input."""
        result = greeter.get_name()
        self.assertEqual(result, 'Alice')
        mock_input.assert_called_once_with("What is your name? ")

    @patch('builtins.input', return_value='  Bob  ')
    def test_get_name_with_whitespace(self, mock_input):
        """Test get_name strips leading and trailing whitespace."""
        result = greeter.get_name()
        self.assertEqual(result, 'Bob')

    @patch('builtins.input', return_value='')
    def test_get_name_empty_input(self, mock_input):
        """Test get_name with empty input."""
        result = greeter.get_name()
        self.assertEqual(result, '')

    @patch('builtins.input', return_value='   ')
    def test_get_name_whitespace_only(self, mock_input):
        """Test get_name with whitespace-only input."""
        result = greeter.get_name()
        self.assertEqual(result, '')

    @patch('builtins.input', return_value='María José')
    def test_get_name_with_special_characters(self, mock_input):
        """Test get_name with accented characters and spaces."""
        result = greeter.get_name()
        self.assertEqual(result, 'María José')


class TestGreet(unittest.TestCase):
    """Test cases for the greet() function."""

    def test_greet_simple_name(self):
        """Test greet with a simple name."""
        result = greeter.greet('Alice')
        self.assertEqual(result, 'Hello, Alice!')

    def test_greet_name_with_spaces(self):
        """Test greet with a name containing spaces."""
        result = greeter.greet('John Doe')
        self.assertEqual(result, 'Hello, John Doe!')

    def test_greet_empty_string(self):
        """Test greet with empty string."""
        result = greeter.greet('')
        self.assertEqual(result, 'Hello, !')

    def test_greet_special_characters(self):
        """Test greet with special characters."""
        result = greeter.greet('José-María')
        self.assertEqual(result, 'Hello, José-María!')

    def test_greet_unicode_characters(self):
        """Test greet with Unicode characters."""
        result = greeter.greet('李明')
        self.assertEqual(result, 'Hello, 李明!')

    def test_greet_very_long_name(self):
        """Test greet with a very long name."""
        long_name = 'A' * 100
        result = greeter.greet(long_name)
        self.assertEqual(result, f'Hello, {long_name}!')


class TestMain(unittest.TestCase):
    """Test cases for the main() function integration."""

    @patch('builtins.input', return_value='Alice')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_with_name(self, mock_stdout, mock_input):
        """Test main function with valid name input."""
        greeter.main()
        output = mock_stdout.getvalue()
        self.assertEqual(output.strip(), 'Hello, Alice!')

    @patch('builtins.input', return_value='')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_with_empty_input(self, mock_stdout, mock_input):
        """Test main function with empty input."""
        greeter.main()
        output = mock_stdout.getvalue()
        self.assertEqual(output.strip(), 'Hello, there!')

    @patch('builtins.input', return_value='   ')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_with_whitespace_only(self, mock_stdout, mock_input):
        """Test main function with whitespace-only input."""
        greeter.main()
        output = mock_stdout.getvalue()
        self.assertEqual(output.strip(), 'Hello, there!')

    @patch('builtins.input', return_value='  Bob  ')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_strips_whitespace(self, mock_stdout, mock_input):
        """Test main function strips whitespace from input."""
        greeter.main()
        output = mock_stdout.getvalue()
        self.assertEqual(output.strip(), 'Hello, Bob!')


class TestEdgeCases(unittest.TestCase):
    """Test cases for edge cases and boundary conditions."""

    def test_greet_numeric_string(self):
        """Test greet with numeric string (valid input)."""
        result = greeter.greet('12345')
        self.assertEqual(result, 'Hello, 12345!')

    def test_greet_symbols(self):
        """Test greet with symbols."""
        result = greeter.greet('@#$%')
        self.assertEqual(result, 'Hello, @#$%!')

    @patch('builtins.input', return_value='O\'Brien')
    def test_get_name_with_apostrophe(self, mock_input):
        """Test get_name with apostrophe in name."""
        result = greeter.get_name()
        self.assertEqual(result, "O'Brien")

    @patch('builtins.input', return_value='Anne-Marie')
    def test_get_name_with_hyphen(self, mock_input):
        """Test get_name with hyphenated name."""
        result = greeter.get_name()
        self.assertEqual(result, 'Anne-Marie')


if __name__ == '__main__':
    unittest.main()
