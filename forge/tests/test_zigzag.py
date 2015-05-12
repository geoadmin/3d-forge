# -*- coding: utf-8 -*-

import unittest
from forge.lib.helpers import numberToZigZag, zigZagToNumber


class TestZigZag(unittest.TestCase):

    def testTo(self):
        self.assertEqual(numberToZigZag(-1), 1)
        self.assertEqual(numberToZigZag(-2), 3)
        self.assertEqual(numberToZigZag(0), 0)
        self.assertEqual(numberToZigZag(1), 2)
        self.assertEqual(numberToZigZag(2), 4)
        self.assertEqual(numberToZigZag(-1000000), 1999999)
        self.assertEqual(numberToZigZag(1000000), 2000000)

    def testBoth(self):
        self.assertEqual(-1, zigZagToNumber(numberToZigZag(-1)))
        self.assertEqual(-2, zigZagToNumber(numberToZigZag(-2)))
        self.assertEqual(0, zigZagToNumber(numberToZigZag(0)))
        self.assertEqual(1, zigZagToNumber(numberToZigZag(1)))
        self.assertEqual(2, zigZagToNumber(numberToZigZag(2)))
        self.assertEqual(-10000, zigZagToNumber(numberToZigZag(-10000)))
        self.assertEqual(10000, zigZagToNumber(numberToZigZag(10000)))

        self.assertEqual(0, numberToZigZag(zigZagToNumber(0)))
        self.assertEqual(1, numberToZigZag(zigZagToNumber(1)))
        self.assertEqual(2, numberToZigZag(zigZagToNumber(2)))
        self.assertEqual(2000000, numberToZigZag(zigZagToNumber(2000000)))
