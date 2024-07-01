from unittest import TestCase
from teql import TEQL
from teql import ast
import os

class EvaluateSelectionsTest(TestCase):
    def setUp(self):
        os.chdir(os.path.join(os.path.dirname(__file__)))
        self.teql = TEQL()
        self.teql.use = 'files/aristotle.html'
        self.context = next(self.teql._iterFileContexts())[1]

    def test_find_selection_string(self):
        results = list(self.teql._evaluateSelection(ast.FindSelection("Virtue"), self.context))
        self.assertEqual(len(results), 126, '126 matches (case sensitive)')
        self.assertEqual(len(results[0]), 6)
        self.assertEqual(results[0].string(), 'Virtue')

    def test_find_selection_regex(self):
        results = list(self.teql._evaluateSelection(ast.FindSelection(ast.LiteralRegex("virtue", 'i')), self.context))
        self.assertEqual(len(results), 253, '253 matches (case insensitive)')
        self.assertEqual(len(results[0]), 6)
        self.assertEqual(results[0].string(), 'virtue')
    
    def test_file_selection(self):
        results = list(self.teql._evaluateSelection(ast.FileSelection(), self.context.sub(6, 7)))
        self.assertEqual(len(results), 1, 'Should select whole file in single selection')
        self.assertEqual(results[0].start, 0)
        self.assertEqual(results[0].end, 718919)

    def test_direct_line_selection_index(self):
        results = list(self.teql._evaluateSelection(ast.DirectLineSelection([ast.RangeIndexIndex(2549)]), self.context))
        self.assertEqual(len(results), 1, 'Should select a single line')
        self.assertEqual(results[0].string(), "I. In respect of truth:\n")

    def test_direct_line_selection_first(self):
        results = list(self.teql._evaluateSelection(ast.DirectLineSelection([ast.RangeIndexFirst(3)]), self.context))
        self.assertEqual(len(results), 3, 'Should select first three lines')
        self.assertEqual(results[0].string(), '<!DOCTYPE html>\n')
        self.assertEqual(results[1].string(), '<html lang="en">\n')
        self.assertEqual(results[2].string(), '<head>\n')

    def test_direct_line_selection_last(self):
        results = list(self.teql._evaluateSelection(ast.DirectLineSelection([ast.RangeIndexLast(3)]), self.context))
        self.assertEqual(len(results), 3, 'Should select last three lines')
        self.assertEqual(results[0].string(), '\n')
        self.assertEqual(results[1].string(), '</section></body>\n')
        self.assertEqual(results[2].string(), '</html>\n')

    def test_direct_line_selection_range(self):
        results = list(self.teql._evaluateSelection(ast.DirectLineSelection([ast.RangeIndexRange(1234,1237)]), self.context))
        self.assertEqual(len(results), 4, 'Should select four lines (1234, 1235, 1236, 1237)')
        self.assertEqual(results[0].string(), "He is best of all who of himself conceiveth all things;<br>\n")
        self.assertEqual(results[1].string(), "Good again is he too who can adopt a good suggestion;<br>\n")
        self.assertEqual(results[2].string(), "But whoso neither of himself conceiveth nor hearing from another<br>\n")
        self.assertEqual(results[3].string(), "Layeth it to heart;—he is a useless man.\n")

    def test_direct_line_selection_next(self):
        results = list(self.teql._evaluateSelection(ast.DirectLineSelection([ast.RangeIndexIndex(3248), ast.RangeIndexNext()]), self.context))
        self.assertEqual(len(results), 2, 'Should select two lines (3248, 3249)')
        self.assertEqual(results[0].string(), "As for the plea, that a man did not know that habits are produced from separate\n")
        self.assertEqual(results[1].string(), "acts of working, we reply, such ignorance is a mark of excessive stupidity.\n")

    def test_selection_line_selection(self):
        results = list(self.teql._evaluateSelection(ast.SelectionLineSelection(ast.FileSelection()), self.context))
        self.assertEqual(len(results), 13245, 'Should select each individual line of file')

    def test_before_selection(self):
        results = list(self.teql._evaluateSelection(ast.SelectionBeforeSelection(ast.DirectLineSelection([ast.RangeIndexIndex(4)])), self.context))
        self.assertEqual(len(results), 1, 'Should produce single selection block')
        self.assertEqual(results[0].string(), '<!DOCTYPE html>\n<html lang="en">\n<head>\n', 'Should select everything before line 4 (e.g. first three lines)')

    def test_after_selection(self):
        results = list(self.teql._evaluateSelection(ast.SelectionAfterSelection(ast.DirectLineSelection([ast.RangeIndexIndex(13242)])), self.context))
        self.assertEqual(len(results), 1, 'Should produce a single selection block')
        self.assertEqual(results[0].string(), '\n</section></body>\n</html>\n', 'Should select everything after line 13242 (e.g. last three lines)')

    def test_cursor_line_selection(self):
        results = list(self.teql._evaluateSelection(ast.CursorLineSelection(ast.StartCursor()), self.context))
        self.assertEqual(len(results), 1, 'Should select single line (First line)')
        self.assertEqual(results[0].string(), '<!DOCTYPE html>\n')

    def test_block_selection(self):
        results = list(self.teql._evaluateSelection(ast.BlockSelection(
            ast.DirectLineSelection([ast.RangeIndexIndex(3251)]),
            ast.DirectLineSelection([ast.RangeIndexIndex(3267)]),
        ), self.context))
        self.assertEqual(len(results), 1, 'Should produce a single selection block')
        self.assertEqual(results[0].string(), """<p>
Furthermore, it is wholly irrelevant to say that the man who acts unjustly or
dissolutely does not <i>wish</i> to attain the habits of these vices: for if a
man wittingly does those things whereby he must become unjust he is to all
intents and purposes unjust voluntarily; but he cannot with a wish cease to be
unjust and become just. For, to take the analogous case, the sick man cannot
with a wish be well again, yet in a supposable case he is voluntarily ill
because he has produced his sickness by living intemperately and disregarding
his physicians. There was a time then when he might have helped being ill, but
now he has let himself go he cannot any longer; just as he who has let a stone
out of his hand cannot recall it,<a href="#fn-3.14" id="fnref-3.14" class="pginternal"><sup>[14]</sup></a>
and yet it rested with him to aim and throw it, because the origination was in
his power. Just so the unjust man, and he who has lost all self-control, might
originally have helped being what they are, and so they are voluntarily what
they are; but now that they are become so they no longer have the power of
being otherwise.
</p>
""")
        
    def test_between_selection(self):
        results = list(self.teql._evaluateSelection(ast.BetweenSelection(
            ast.DirectLineSelection([ast.RangeIndexIndex(3207)]),
            ast.DirectLineSelection([ast.RangeIndexIndex(3213)]),
        ), self.context))
        self.assertEqual(len(results), 1, 'Should produce a single selection block')
        self.assertEqual(results[0].string(), """<p>
But if this is matter of plain manifest fact, and we cannot refer our actions
to any other originations beside those in our own power, those things must be
in our own power, and so voluntary, the originations of which are in ourselves.
</p>
""")
    def test_range_index_selection(self):
        results = list(self.teql._evaluateSelection(ast.RangeIndexSelection([ast.RangeIndexRange(5446, 5450)], ast.SelectionLineSelection(ast.FileSelection())), self.context))
        self.assertEqual(len(results), 5, 'Should select 5 lines (5446, 5447, 5448, 5449, 5450)')
        self.assertEqual(results[0].string(), 'And among whomsoever there is the possibility of injustice among these there is\n')
        self.assertEqual(results[1].string(), 'that of acting unjustly; but it does not hold conversely that injustice\n')
        self.assertEqual(results[2].string(), 'attaches to all among whom there is the possibility of acting unjustly, since\n')
        self.assertEqual(results[3].string(), 'by the former we mean giving one’s self the larger share of what is\n')
        self.assertEqual(results[4].string(), 'abstractedly good and the less of what is abstractedly evil.\n')

    def test_sub_selection(self):
        results = list(self.teql._evaluateSelection(ast.SubSelection(ast.FindSelection('sweet'), ast.DirectLineSelection([ast.RangeIndexIndex(7120)])), self.context))
        self.assertEqual(len(results), 1, 'Only one instance of the word is on this line')
        self.assertEqual(results[0].string(), 'sweet')

    def test_substring_selection(self):
        results = list(self.teql._evaluateSelection(ast.SubstringSelection(389566, 389579), self.context))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].string(), 'This is sweet')
    
    def test_start_cursor(self):
        results = list(self.teql._evaluateSelection(ast.StartCursor(), self.context))
        self.assertEqual(len(results), 1, 'One cursor is returned')
        self.assertEqual(len(results[0]), 0, 'The selection is a cursor (no length)')
        self.assertEqual(results[0].start, 0, 'Cursor at beginning of file')

    def test_end_cursor(self):
        results = list(self.teql._evaluateSelection(ast.EndCursor(), self.context))
        self.assertEqual(len(results), 1, 'One cursor is returned')
        self.assertEqual(len(results[0]), 0, 'The selection is a cursor (no length)')
        self.assertEqual(results[0].start, 718919, 'Cursor at end of file')

    def test_seek_cursor(self):
        results = list(self.teql._evaluateSelection(ast.SeekCursor(1234), self.context))
        self.assertEqual(len(results), 1, 'One cursor is returned')
        self.assertEqual(len(results[0]), 0, 'The selection is a cursor (no length)')
        self.assertEqual(results[0].start, 1234, 'Cursor at the specified location')

    def test_seek_cursor_negative(self):
        results = list(self.teql._evaluateSelection(ast.SeekCursor(-12), self.context))
        self.assertEqual(len(results), 1, 'One cursor is returned')
        self.assertEqual(len(results[0]), 0, 'The selection is a cursor (no length)')
        self.assertEqual(results[0].start, 718907, 'Cursor at the specified location')

    def test_offset_cursor(self):
        results = list(self.teql._evaluateSelection(ast.OffsetCursor(12, ast.StartCursor()), self.context))
        self.assertEqual(len(results), 1, 'One cursor is returned')
        self.assertEqual(len(results[0]), 0, 'The selection is a cursor (no length)')
        self.assertEqual(results[0].start, 12, 'Cursor at the specified location')

    def test_offset_cursor_negative(self):
        results = list(self.teql._evaluateSelection(ast.OffsetCursor(-12, ast.EndCursor()), self.context))
        self.assertEqual(len(results), 1, 'One cursor is returned')
        self.assertEqual(len(results[0]), 0, 'The selection is a cursor (no length)')
        self.assertEqual(results[0].start, 718907, 'Cursor at the specified location')

    def test_before_cursor(self):
        results = list(self.teql._evaluateSelection(ast.SelectionBeforeCursor(12, ast.EndCursor()), self.context))
        self.assertEqual(len(results), 1, 'One cursor is returned')
        self.assertEqual(len(results[0]), 0, 'The selection is a cursor (no length)')
        self.assertEqual(results[0].start, 718907, 'Cursor at the specified location')

    def test_offset_cursor(self):
        results = list(self.teql._evaluateSelection(ast.SelectionAfterCursor(12, ast.StartCursor()), self.context))
        self.assertEqual(len(results), 1, 'One cursor is returned')
        self.assertEqual(len(results[0]), 0, 'The selection is a cursor (no length)')
        self.assertEqual(results[0].start, 12, 'Cursor at the specified location')
