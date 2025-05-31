#!/usr/bin/env python3
"""Simple tests to ensure all's well."""

import unittest
from pathlib import Path

import respond_to_issues

class Test(unittest.TestCase):
    # It's expected that most changes to this repo will be to the rotation file,
    # so have a test verifying that it still parses, just in case...
    def test_yaml_parses(self):
        respond_to_issues.parse_rotation_yaml(respond_to_issues.ROTATION_FILE)
        assert False


if __name__ == '__main__':
    unittest.main()

