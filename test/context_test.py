from unittest import TestCase
from teql.context import Context
import os

class ContextTest(TestCase):
    def test_split_lines(self):
        data = "line1\nline2\nline3"
        context = Context(data)
        self.assertEqual(list(context.split_lines_string()), [
            "line1\n","line2\n","line3"
        ])

    def test_split_lines_no_eol(self):
        data = "line1\nline2\nline3\n"
        context = Context(data)
        self.assertEqual(list(context.split_lines_string()), [
            "line1\n","line2\n","line3\n"
        ])
    
    def test_expand_to_lines(self):
        data = "line1\nline2\nline3\n"
        context = Context(data, start=2, end=16)
        self.assertEqual(context.expand_to_lines().string(), data)

    def test_expand_to_lines_no_eol(self):
        data = "line1\nline2\nline3"
        context = Context(data, start=2, end=16)
        self.assertEqual(context.expand_to_lines().string(), data)

    def test_expand_to_lines_already_fit(self):
        data = "line1\nline2\nline3\n"
        context = Context(data, start=6, end=12)
        self.assertEqual(context.expand_to_lines().string(), "line2\n")
    
    def test_find(self):
        data = "let's look for a needle in a haystack"
        context = Context(data)
        found = context.find('needle')
        self.assertEqual(found.start, 17)
        self.assertEqual(found.end, 23)
        self.assertEqual(found.string(), 'needle')

    def test_find_all(self):
        data = "Worn and torn, those forlorn Norn born of Bjorn hath sworn upon the horn and shorn the corn"
        context = Context(data)
        found = list(context.find_all('orn'))
        self.assertEqual(len(found), 10)