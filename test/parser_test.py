from unittest import TestCase
import teql.grammar as g
import teql.parse_nodes as n

class ParserTest(TestCase):

    def test_start_end_cursor(self):
        result = g.CURSOR.parse_string('START').pop()
        self.assertIsInstance(result, n.IndexCursor)
        self.assertEqual(result.index, 0)
        result = g.CURSOR.parse_string('END').pop()
        self.assertIsInstance(result, n.IndexCursor)
        self.assertEqual(result.index, -1)
    
    def test_direct_line_selection(self):
        result = g.SELECTION.parse_string('LINE 2').pop()
        self.assertIsInstance(result, n.DirectLineSelection)
        self.assertEqual(result.line, 2)
        result = g.SELECTION.parse_string('LINE -5').pop()
        self.assertIsInstance(result, n.DirectLineSelection)
        self.assertEqual(result.line, -5)

    def test_find_selection(self):
        result = g.SELECTION.parse_string('FIND "money"').pop()
        self.assertIsInstance(result, n.FindSelection)
        self.assertIsInstance(result.criteria, n.LiteralString)
        self.assertEqual(result.criteria.value, "money")
        self.assertFalse(result.match_line)
        self.assertFalse(result.select_line)
        result = g.SELECTION.parse_string(r'FIND /\$\d+(\.\d{2})?/').pop()
        self.assertIsInstance(result, n.FindSelection)
        self.assertIsInstance(result.criteria, n.LiteralRegex)
        self.assertEqual(result.criteria.value, r"\$\d+(\.\d{2})?")
        self.assertFalse(result.match_line)
        self.assertFalse(result.select_line)
        # result = g.SELECTION.parse_string('FIND LINE "rich uncle"').pop()
        # self.assertIsInstance(result, n.FindSelection)
        # self.assertIsInstance(result.criteria, n.LiteralString)
        # self.assertEqual(result.criteria.value, "rich uncle")
        # self.assertTrue(result.match_line)
        result = g.SELECTION.parse_string('FIND LINE WITH "mansion"').pop()
        self.assertIsInstance(result, n.FindSelection)
        self.assertIsInstance(result.criteria, n.LiteralString)
        self.assertEqual(result.criteria.value, "mansion")
        self.assertFalse(result.match_line)
        self.assertTrue(result.select_line)
        result = g.SELECTION.parse_string('FIND LINE WITH $millions').pop()
        self.assertIsInstance(result, n.FindSelection)
        self.assertIsInstance(result.criteria, n.Variable)
        self.assertEqual(result.criteria.name, "millions")
        self.assertFalse(result.match_line)
        self.assertTrue(result.select_line)
        print(result)

    # def test_before_after_cursor(self):
    #     result = g.CURSOR.parse_string('AFTER LINE 1').pop()
    #     self.assertIsInstance(result, n.RelativeCursor)
    #     self.assertEqual(result.offset, 1)
    #     self.assertEqual(result.from_end, True)
    #     result = g.CURSOR.parse_string('BEFORE LINE 5').pop()
    #     self.assertIsInstance(result, n.RelativeCursor)
    #     self.assertEqual(result.offset, -1)
    #     self.assertEqual(result.from_end, False)
        
