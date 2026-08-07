"""Synthetic replay classifier tests."""

import unittest

import signaling
from replay import classify_mandatory, MANDATORY_START


class TestReplay(unittest.TestCase):
  def test_mandatory_rejection(self):
    version = 0x20000000  # versionbits top but bit 4 clear
    self.assertEqual(
      classify_mandatory(version, MANDATORY_START),
      "mandatory_signaling",
    )

  def test_before_mandatory_no_rejection(self):
    version = 0x20000000
    self.assertIsNone(classify_mandatory(version, MANDATORY_START - 1))

  def test_signaling_ok(self):
    version = 0x20000010
    self.assertIsNone(classify_mandatory(version, MANDATORY_START))


if __name__ == "__main__":
  unittest.main()
