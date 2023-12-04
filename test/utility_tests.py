from unittest import TestCase
from teql.range import apply_ranges
from teql import ast

class ApplyRangesTest(TestCase):
    def test_first(self):
        sample = list(range(10))
        result = apply_ranges([ast.RangeIndexFirst()], sample)
        self.assertEqual(list(result), [0])
        result = apply_ranges([ast.RangeIndexFirst(3)], sample)
        self.assertEqual(list(result), [0, 1, 2])
        # Ensure next is also set
        result = apply_ranges([ast.RangeIndexFirst(), ast.RangeIndexNext()], sample)
        self.assertEqual(list(result), [0, 1])

    def test_last(self):
        sample = list(range(10))
        result = apply_ranges([ast.RangeIndexLast()], sample)
        self.assertEqual(list(result), [9])
        result = apply_ranges([ast.RangeIndexLast(3)], sample)
        self.assertEqual(list(result), [7, 8, 9])
        # Ensure next is also set
        with self.assertRaises(IndexError):
            list(apply_ranges([ast.RangeIndexLast(), ast.RangeIndexNext()], sample))
        
        
    def test_next(self):
        sample = list(range(10))
        # by default next performs like first
        result = apply_ranges([ast.RangeIndexNext()], sample)
        self.assertEqual(list(result), [0])
        result = apply_ranges([ast.RangeIndexNext(3)], sample)
        self.assertEqual(list(result), [0, 1, 2])
        result = apply_ranges([ast.RangeIndexNext(), ast.RangeIndexNext()], sample)
        self.assertEqual(list(result), [0, 1])
        result = apply_ranges([ast.RangeIndexNext(2), ast.RangeIndexNext()], sample)
        self.assertEqual(list(result), [0, 1, 2])
        result = apply_ranges([ast.RangeIndexNext(2), ast.RangeIndexNext(2)], sample)
        self.assertEqual(list(result), [0, 1, 2, 3])

    def test_index(self):
        sample = list(range(10))
        result = apply_ranges([ast.RangeIndexIndex(3)], sample)
        self.assertEqual(list(result), [3])
        # Ensure next is also set
        result = apply_ranges([ast.RangeIndexIndex(3), ast.RangeIndexNext()], sample)
        self.assertEqual(list(result), [3, 4])

    def test_index(self):
        sample = list(range(10))
        result = apply_ranges([ast.RangeIndexRange(3, 5)], sample)
        self.assertEqual(list(result), [3, 4])
        result = apply_ranges([ast.RangeIndexRange(3, 15)], sample)
        self.assertEqual(list(result), [3, 4, 5, 6, 7, 8, 9])
        # Ensure next is also set
        result = apply_ranges([ast.RangeIndexRange(3, 5), ast.RangeIndexNext()], sample)
        self.assertEqual(list(result), [3, 4, 5])

    def test_index_w_step(self):
        sample = list(range(10))
        result = apply_ranges([ast.RangeIndexRange(3, 8, 2)], sample)
        self.assertEqual(list(result), [3, 5, 7])
        result = apply_ranges([ast.RangeIndexRange(3, 18, 2)], sample)
        self.assertEqual(list(result), [3, 5, 7, 9])
        # Ensure next is also set
        result = apply_ranges([ast.RangeIndexRange(3, 8, 2), ast.RangeIndexNext()], sample)
        self.assertEqual(list(result), [3, 5, 7, 8])