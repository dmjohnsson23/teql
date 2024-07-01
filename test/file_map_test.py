from teql.file_map import FileMap
import os
from unittest import TestCase
class FileMapTest(TestCase):
    def setUp(self):
        with open(os.path.join(os.path.dirname(__file__), 'files/jabberwocky.txt') ,'rb') as file:
            self.file_map = FileMap.from_lines(file)

    def test_cursor_at_zero(self):
        self.assertEqual(self.file_map.cursor_to_line_col(0), (1,1))

    def test_cursor_on_first_line(self):
        self.assertEqual(self.file_map.cursor_to_line_col(4), (1,5))

    def test_cursor_on_second_line(self):
        self.assertEqual(self.file_map.cursor_to_line_col(50), (2,15))

    def test_cursor_on_last_line(self):
        self.assertEqual(self.file_map.cursor_to_line_col(999), (34,17))

    def test_cursor_at_end(self):
        # TODO: fails because example file doesn't end with an actual newline
        self.assertEqual(self.file_map.cursor_to_line_col(1017), (34,35))

    def test_line_col_at_1_1(self):
        self.assertEqual(self.file_map.line_col_to_cursor(1,1), 0)

    def test_line_col_on_first_line(self):
        self.assertEqual(self.file_map.line_col_to_cursor(1,5), 4)

    def test_line_col_on_second_line(self):
        self.assertEqual(self.file_map.line_col_to_cursor(2,15), 50)

    def test_line_col_on_last_line(self):
        self.assertEqual(self.file_map.line_col_to_cursor(34,17), 999)

    def test_line_col_at_end(self):
        pass # TODO

    def test_line_col_after_eol(self):
        pass # TODO

    def test_line_len_first(self):
        self.assertEqual(self.file_map.line_length(1), 36) # 35 + EOL

    def test_line_len_in_middle(self):
        self.assertEqual(self.file_map.line_length(7), 48) # 47 + EOL

    def test_line_len_last(self):
        self.assertEqual(self.file_map.line_length(34), 34) # Line has no EOL character

    def test_line_to_start_end_cursor_first(self):
        self.assertEqual(self.file_map.line_to_start_end_cursor(1), (0, 36))

    def test_line_to_start_end_cursor_in_middle(self):
        self.assertEqual(self.file_map.line_to_start_end_cursor(7), (173,221))

    def test_line_to_start_end_cursor_last(self):
        self.assertEqual(self.file_map.line_to_start_end_cursor(34), (983,1017))
    
        