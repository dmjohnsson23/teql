# from unittest import TestCase
# from teql.parser import parse
# from teql import ast

# class ParserTest(TestCase):
#     def test_parse_select_find_string(self):
#         result = parse('SELECT FIND "good stuff" FROM file.txt')
#         self.assertEqual(result, [ast.SelectQuery(
#             values=[ast.SelectValue(
#                     value=ast.FindSelection('good stuff'),
#                     alias=None
#             )], 
#             path='file.txt'
#         )])


#     def test_start_end_cursor(self):
#         result = parse('SELECT FROM START TO END FROM file.txt')
#         self.assertEqual(result, [ast.SelectQuery(
#             values=[ast.SelectValue(
#                 value=ast.BlockSelection(
#                     start=ast.StartCursor(), 
#                     end=ast.EndCursor()
#                 ), 
#             )],
#             path='file.txt'
#         )])
    
#     def test_direct_line_selections(self):
#         result = parse('SELECT LINE 2 FROM file.txt ; SELECT LINE -5 FROM file.txt')
#         self.assertEqual(result, [
#             ast.SelectQuery(
#                 values=[ast.SelectValue(
#                     value=ast.DirectLineSelection(ranges=[ast.RangeIndexIndex(index=2)])
#                 )],
#                 path='file.txt'
#             ),
#             ast.SelectQuery(
#                 values=[ast.SelectValue(
#                     value=ast.DirectLineSelection(ranges=[ast.RangeIndexIndex(index=-5)])
#                 )],
#                 path='file.txt'
#             ),
#         ])

#     def test_find_selection(self):
#         result = parse(r'SELECT FIND "money", FIND /\$\d+(\.\d{2})?/, FIND LINE "rich uncle", FIND LINE WITH "mansion", FIND LINE WITH $millions FROM file.txt')
        # self.assertEqual(result, [
        #     ast.SelectQuery(values=[
        #         ast.SelectValue(value=ast.FindSelection('money', is_next=False, is_matching=False, is_line=False, is_with=False), alias=None),
        #         ast.SelectValue(value=ast.FindSelection(re.compile('\\$\\d+(\\.\\d{2})?'), is_next=False, is_matching=False, is_line=False, is_with=False), alias=None), 
        #         ast.SelectValue(value=ast.FindSelection('rich uncle', is_next=False, is_matching=False, is_line=True, is_with=False), alias=None), 
        #         ast.SelectValue(value=ast.FindSelection('mansion', is_next=False, is_matching=False, is_line=True, is_with=True), alias=None), 
        #         ast.SelectValue(value=ast.FindSelection(ast.Variable(identifiers=['millions']), is_next=False, is_matching=False, is_line=True, is_with=True), alias=None)
        #     ],
        #     path='file.txt')
        # ])

    # def test_before_after_cursor(self):
    #     result = g.CURSOR.parse_string('AFTER LINE 1').pop()
    #     self.assertIsInstance(result, n.RelativeCursor)
    #     self.assertEqual(result.offset, 1)
    #     self.assertEqual(result.from_end, True)
    #     result = g.CURSOR.parse_string('BEFORE LINE 5').pop()
    #     self.assertIsInstance(result, n.RelativeCursor)
    #     self.assertEqual(result.offset, -1)
    #     self.assertEqual(result.from_end, False)
        
