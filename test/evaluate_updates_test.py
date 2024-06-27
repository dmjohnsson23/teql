from unittest import TestCase
from teql import TEQL
from teql import ast
from teql.operation import Opcode, Operation
import os

class EvaluateUpdatesTest(TestCase):
    def setUp(self):
        os.chdir(os.path.join(os.path.dirname(__file__)))
        self.teql = TEQL()
        self.teql.use = 'files/jabberwocky.txt'
        self.context = next(self.teql._iterFileContexts())

    def test_find_replace(self):
        # CHANGE 'mimsy' TO 'miserable and flimsy'
        editor = self.teql._evaluateUpdateQuery(ast.ChangeQuery(ast.FindSelection('mimsy'), "miserable and flimsy"))
        self.assertEqual(list(editor.operations), [
            Opcode.replace(79, 84, "miserable and flimsy"),
            Opcode.replace(957, 962, "miserable and flimsy"),
        ])

    def test_truncate(self):
        # DELETE EVERYTHING AFTER LINE 29
        editor = self.teql._evaluateUpdateQuery(ast.DeleteQuery(ast.SelectionAfterSelection(ast.DirectLineSelection([ast.RangeIndexIndex(29)]))))
        self.assertEqual(list(editor.operations), [
            Opcode.delete(877, 1017),
        ])