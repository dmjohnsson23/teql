from unittest import TestCase
from teql.context import Context
from teql.operation import Opcode
from teql.editor import Editor, EditorError
import os

class EditorTest(TestCase):
    def test_insert_at_start(self):
        context = Context(b'1234567890')
        ops = (Opcode.insert(0, 0, 'a'),)
        b''.join(Editor(context, ops))
        self.assertEqual(b''.join(Editor(context, ops)), b'a1234567890')

    def test_insert_in_middle(self):
        context = Context(b'1234567890')
        ops = (Opcode.insert(5, 5, 'a'),)
        b''.join(Editor(context, ops))
        self.assertEqual(b''.join(Editor(context, ops)), b'12345a67890')

    def test_insert_at_end(self):
        context = Context(b'1234567890')
        ops = (Opcode.insert(10, 10, 'a'),)
        b''.join(Editor(context, ops))
        self.assertEqual(b''.join(Editor(context, ops)), b'1234567890a')

    def test_replace_at_start(self):
        context = Context(b'1234567890')
        ops = (Opcode.replace(0, 1, 'a'),)
        b''.join(Editor(context, ops))
        self.assertEqual(b''.join(Editor(context, ops)), b'a234567890')

    def test_replace_in_middle(self):
        context = Context(b'1234567890')
        ops = (Opcode.replace(5, 6, 'a'),)
        b''.join(Editor(context, ops))
        self.assertEqual(b''.join(Editor(context, ops)), b'12345a7890')

    def test_replace_at_end(self):
        context = Context(b'1234567890')
        ops = (Opcode.replace(9, 10, 'a'),)
        b''.join(Editor(context, ops))
        self.assertEqual(b''.join(Editor(context, ops)), b'123456789a')

    def test_replace_larger(self):
        context = Context(b'1234567890')
        ops = (Opcode.replace(3, 4, 'abcdefg'),)
        b''.join(Editor(context, ops))
        self.assertEqual(b''.join(Editor(context, ops)), b'123abcdefg567890')

    def test_replace_smaller(self):
        context = Context(b'1234567890')
        ops = (Opcode.replace(3, 8, 'a'),)
        b''.join(Editor(context, ops))
        self.assertEqual(b''.join(Editor(context, ops)), b'123a90')

    def test_delete_at_start(self):
        context = Context(b'1234567890')
        ops = (Opcode.delete(0, 2),)
        b''.join(Editor(context, ops))
        self.assertEqual(b''.join(Editor(context, ops)), b'34567890')

    def test_delete_in_middle(self):
        context = Context(b'1234567890')
        ops = (Opcode.delete(5, 8),)
        b''.join(Editor(context, ops))
        self.assertEqual(b''.join(Editor(context, ops)), b'1234590')

    def test_delete_at_end(self):
        context = Context(b'1234567890')
        ops = (Opcode.delete(8, 10),)
        b''.join(Editor(context, ops))
        self.assertEqual(b''.join(Editor(context, ops)), b'12345678')

    def test_multiple(self):
        context = Context(b'1234567890')
        ops = (Opcode.replace(2, 5, 'a'), Opcode.delete(8, 10),)
        b''.join(Editor(context, ops))
        self.assertEqual(b''.join(Editor(context, ops)), b'12a678')

    def test_multiple_touching(self):
        context = Context(b'1234567890')
        ops = (Opcode.replace(7, 8, 'a'), Opcode.delete(8, 10),)
        b''.join(Editor(context, ops))
        self.assertEqual(b''.join(Editor(context, ops)), b'1234567a')

    def test_multiple_overlapping(self):
        with self.assertRaises(EditorError):
            context = Context(b'1234567890')
            ops = (Opcode.replace(7, 9, 'a'), Opcode.delete(8, 10),)
            b''.join(Editor(context, ops))