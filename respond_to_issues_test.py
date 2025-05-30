#!/usr/bin/env python3
"""Simple tests to ensure all's well."""

import unittest
from pathlib import Path

import respond_to_issues

MY_DIR = Path(__file__).resolve().parent

class Test(unittest.TestCase):
    def test_yaml_parses(self):
        respond_to_issues.parse_rotation_yaml(MY_DIR / "rotation.yaml")


if __name__ == '__main__':
    unittest.main()

