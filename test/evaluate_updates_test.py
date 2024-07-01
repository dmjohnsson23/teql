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
        # CHANGE FIND 'mimsy' TO 'miserable and flimsy';
        result = self.teql._evaluateUpdateQuery(ast.ChangeQuery(ast.FindSelection('mimsy'), "miserable and flimsy"))
        editor = list(result)[0][1]
        self.assertEqual(list(editor.operations), [
            Opcode.replace(79, 84, "miserable and flimsy"),
            Opcode.replace(957, 962, "miserable and flimsy"),
        ])

    def test_truncate(self):
        # DELETE EVERYTHING AFTER LINE 29;
        result = self.teql._evaluateUpdateQuery(ast.DeleteQuery(ast.SelectionAfterSelection(ast.DirectLineSelection([ast.RangeIndexIndex(29)]))))
        editor = list(result)[0][1]
        self.assertEqual(list(editor.operations), [
            Opcode.delete(877, 1017),
        ])

    def test_insert(self):
        # INSERT " [gruff, rough-mannered, ill-tempered]" AFTER FIND "uffish";
        result = self.teql._evaluateUpdateQuery(ast.InsertQuery(" [gruff, rough-mannered, ill-tempered]", ast.SelectionAfterCursor(ast.FindSelection("uffish"))))
        editor = list(result)[0][1]
        self.assertEqual(list(editor.operations), [
            Opcode.insert(451, 451, " [gruff, rough-mannered, ill-tempered]"),
        ])