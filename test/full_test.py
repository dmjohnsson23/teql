from unittest import TestCase
from teql import TEQL
import os

class FullTest(TestCase):
    def setUp(self):
        os.chdir(os.path.join(os.path.dirname(__file__)))
        self.teql = TEQL()

    def test_show_find_string(self):
        result = self.teql.execute('SHOW FIND "Virtue" FROM files/aristotle.html').fetch()
        self.assertEqual(len(result[1]._positional), 126)

    def test_show_find_regex(self):
        result = self.teql.execute('SHOW FIND /virtue/i FROM files/aristotle.html').fetch()
        self.assertEqual(len(result[1]._positional), 253)

    def test_show_first_lines(self):
        result = self.teql.execute('SHOW FIRST 3 LINES IN FILE FROM files/aristotle.html').fetch()
        self.assertEqual(result[1][0], 
            '<!DOCTYPE html>\n'
            '<html lang="en">\n'
            '<head>\n'
        )

    def test_show_single_line(self):
        result = self.teql.execute('SHOW LINE 2549 FROM files/aristotle.html').fetch()
        self.assertEqual(result[1][0], 
            "I. In respect of truth:\n"
        )

    def test_show_from_line_to_line(self):
        result = self.teql.execute('SHOW FROM LINE 1234 TO LINE 1237 FROM files/aristotle.html').fetch()
        self.assertEqual(result[1][0], 
            "He is best of all who of himself conceiveth all things;<br>\n"
            "Good again is he too who can adopt a good suggestion;<br>\n"
            "But whoso neither of himself conceiveth nor hearing from another<br>\n"
            "Layeth it to heart;—he is a useless man.\n"
        )

