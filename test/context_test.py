from unittest import TestCase, skip
from teql.context import Context
import os
from tempfile import TemporaryFile
from string import printable

class ContextTest(TestCase):
    @skip('Slow test')
    def test_large_file(self):
        with TemporaryFile('r+') as file:
            for x in range(100000):
                for c in printable:
                    file.write(c*1000)
            context = Context(file)


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

    def test_find_nothing(self):
        data = "let's look for a needle in a haystack"
        context = Context(data)
        found = context.find('beetle')
        self.assertIsNone(found)

    def test_find_2(self):
        data = "let's look for a needle in a haystack (but not *this* needle)"
        context = Context(data)
        found = context.find('needle')
        self.assertEqual(found.start, 17)
        self.assertEqual(found.end, 23)
        self.assertEqual(found.string(), 'needle')

    def test_find_2_substring(self):
        data = "let's look for a needle in a haystack (but not *that* needle)"
        context = Context(data, start=25)
        found = context.find('needle')
        self.assertEqual(found.start, 54)
        self.assertEqual(found.end, 60)
        self.assertEqual(found.string(), 'needle')

    def test_find_all(self):
        data = "Worn and torn, those forlorn Norn born of Bjorn hath sworn upon the horn and shorn the corn"
        context = Context(data)
        found = list(context.find_all('orn'))
        self.assertEqual(len(found), 10)

    def test_find_all_substring(self):
        data = "Worn and torn, those forlorn Norn born of Bjorn hath sworn upon the horn and shorn the corn"
        context = Context(data, start=21, end=33)
        found = list(context.find_all('orn'))
        self.assertEqual(len(found), 2)

    def test_find_re(self):
        data = "let's look for a needle in a haystack"
        context = Context(data)
        found = context.find_re('ne+d.e')
        self.assertEqual(found.start, 17)
        self.assertEqual(found.end, 23)
        self.assertEqual(found.string(), 'needle')

    def test_find_re_2(self):
        data = "let's look for a needle in a haystack (but not *this* needle)"
        context = Context(data)
        found = context.find_re('needle')
        self.assertEqual(found.start, 17)
        self.assertEqual(found.end, 23)
        self.assertEqual(found.string(), 'needle')

    def test_find_re_2_substring(self):
        data = "let's look for a needle in a haystack (but not *that* needle)"
        context = Context(data, start=25)
        found = context.find_re('needle')
        self.assertEqual(found.start, 54)
        self.assertEqual(found.end, 60)
        self.assertEqual(found.string(), 'needle')

    def test_find_all_re(self):
        data = "Worn and torn, those forlorn Norn born of Bjorn hath sworn upon the horn and shorn the corn"
        context = Context(data)
        found = list(context.find_all_re('[A-Za-z]+orn'))
        self.assertEqual(len(found), 10)

    def test_find_all_re_substring(self):
        data = "Worn and torn, those forlorn Norn born of Bjorn hath sworn upon the horn and shorn the corn"
        context = Context(data, start=21, end=33)
        found = list(context.find_all_re('[A-Za-z]+orn'))
        self.assertEqual(len(found), 2)

    def test_sub_of_sub(self):
        data = "Lllama llama / Llama llama / I ride a / Ride a llama"
        context = Context(data, start=21, end=43)
        sub = context.sub(10, 20)
        self.assertEqual(sub.start, 31)
        self.assertEqual(sub.end, 41)

    def test_sub_of_sub_too_long(self):
        with self.assertRaises(IndexError):
            data = "Lllama llama / Llama llama / I ride a / Ride a llama"
            context = Context(data, start=21, end=43)
            context.sub(10, 25)