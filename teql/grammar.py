import pyparsing as p
from . import parse_nodes as n
from ast import literal_eval

COMMENT = p.Suppress((p.Literal('--') - p.rest_of_line) | (p.Literal('//') - p.rest_of_line) | p.Literal('/*') + p.NotAny('*') - p.SkipTo(p.Literal('*/')) - p.Literal('*/'))

VARIABLE = p.Literal('$').suppress() - (p.common.identifier | p.common.integer)
@VARIABLE.set_parse_action
def parse_variable(s, pos, tokens):
    return n.Variable(tokens[0])._parsedata(s, pos)
LITERAL_STRING = p.quoted_string
@LITERAL_STRING.set_parse_action
def parse_literal_string(s, pos, tokens):
    # Hijack python's string parsing
    return n.LiteralString(literal_eval(tokens[0]))._parsedata(s, pos)
LITERAL_REGEX = p.QuotedString('/', '\\', unquote_results=False)
@LITERAL_REGEX.set_parse_action
def parse_literal_regex(s, pos, tokens):
    return n.LiteralRegex(tokens[0][1:-1])._parsedata(s, pos)
LITERAL_INT = p.common.signed_integer
@LITERAL_INT.set_parse_action
def parse_literal_int(s, pos, tokens):
    return n.LiteralInt(int(tokens[0]))._parsedata(s, pos)
LITERAL_FLOAT = p.common.fnumber
@LITERAL_FLOAT.set_parse_action
def parse_literal_float(s, pos, tokens):
    return n.LiteralFloat(tokens[0])._parsedata(s, pos)

CURSOR = p.Forward()
SELECTION = p.Forward()
CURSOR_OR_SELECTION = CURSOR | SELECTION
RANGE_INDEX = p.Keyword('FIRST', caseless=True) - p.Opt(LITERAL_INT) | p.Keyword('NEXT', caseless=True) - p.Opt(LITERAL_INT)  | p.Keyword('LAST', caseless=True) - p.Opt(LITERAL_INT)  | (LITERAL_INT - p.Literal(':').suppress() - LITERAL_INT - p.Opt(p.Literal(':').suppress() - LITERAL_INT )) | LITERAL_INT
@RANGE_INDEX.set_parse_action
def parse_range_index(s, pos, tokens):
    if isinstance(tokens[0], str) and tokens[0].upper() == 'FIRST':
        return n.RangeIndex(0, None if len(tokens) == 1 else tokens[1].value)._parsedata(s, pos)
    elif isinstance(tokens[0], str) and tokens[0].upper() == 'NEXT':
        return n.RangeIndex(None, None if len(tokens) == 1 else tokens[1].value)._parsedata(s, pos)
    elif isinstance(tokens[0], str) and tokens[0].upper() == 'LAST':
        return n.RangeIndex(-1, None if len(tokens) == 1 else -tokens[1].value)._parsedata(s, pos)
    elif isinstance(tokens[0], int):
        return n.RangeIndex(*tokens)._parsedata(s, pos)
RANGE_INDEX_LIST = p.delimited_list(RANGE_INDEX)

# place cursor at the start of the current context
START_CURSOR = p.Keyword('START', caseless=True)
@START_CURSOR.set_parse_action
def parse_start_cursor(s, pos, tokens):
    return n.IndexCursor(0)._parsedata(s, pos)
# place cursor at the end of the current context
END_CURSOR = p.Keyword('END', caseless=True)
@END_CURSOR.set_parse_action
def parse_end_cursor(s, pos, tokens):
    return n.IndexCursor(-1)._parsedata(s, pos)
# place cursor at the after a selection or cursor
SELECTION_AFTER_CURSOR = p.Keyword('AFTER', caseless=True) - CURSOR_OR_SELECTION
@SELECTION_AFTER_CURSOR.set_parse_action
def parse_selection_after_cursor(s, pos, tokens):
    return n.RelativeCursor(0, True, tokens[1])._parsedata(s, pos)
# place cursor before a selection or cursor
SELECTION_BEFORE_CURSOR = p.Keyword('BEFORE', caseless=True) - CURSOR_OR_SELECTION
@SELECTION_BEFORE_CURSOR.set_parse_action
def parse_selection_before_cursor(s, pos, tokens):
    return n.RelativeCursor(-1, False, tokens[1])._parsedata(s, pos)
# place a cursor in the context of a selection
SELECTION_CURSOR = CURSOR - p.Keyword('OF', caseless=True).suppress() - SELECTION
@SELECTION_CURSOR.set_parse_action
def parse_selection_cursor(s, pos, tokens):
    return n.SelectionCursor(*tokens)._parsedata(s, pos)
# if a cursor has multiple matches, select the nth one
RANGE_INDEX_CURSOR = RANGE_INDEX_LIST - CURSOR
@RANGE_INDEX_CURSOR.set_parse_action
def parse_range_index_cursor(s, pos, tokens):
    return n.RangeIndexCursor(*tokens)._parsedata(s, pos)
CURSOR <<= START_CURSOR | END_CURSOR | SELECTION_AFTER_CURSOR | SELECTION_BEFORE_CURSOR | SELECTION_CURSOR | RANGE_INDEX_CURSOR

# select a specific line by line number; negative to select from end
DIRECT_LINE_SELECTION = p.Keyword('LINE', caseless=True).suppress() + LITERAL_INT
@DIRECT_LINE_SELECTION.set_parse_action
def parse_direct_line_selection(s, pos, tokens):
    return n.DirectLineSelection(tokens[0].value)._parsedata(s, pos)
STRING_MATCH_EXPRESSION = LITERAL_STRING | LITERAL_REGEX | VARIABLE | SELECTION
# select a line containing a literal strings
FIND_LINE_WITH_SELECTION =  p.Keyword('FIND', caseless=True).suppress() + p.Keyword('LINE', caseless=True).suppress() + p.Keyword('WITH', caseless=True).suppress() - STRING_MATCH_EXPRESSION
@FIND_LINE_WITH_SELECTION.set_parse_action
def parse_line_with_selection(s, pos, tokens):
    return n.FindSelection(tokens[0], select_line=True)._parsedata(s, pos)
# select a line matching literal string
FIND_LINE_SELECTION = p.Keyword('FIND', caseless=True).suppress() + p.Keyword('LINE', caseless=True).suppress() - STRING_MATCH_EXPRESSION
@FIND_LINE_SELECTION.set_parse_action
def parse_find_line_selection(s, pos, tokens):
    return n.FindSelection(tokens[0], match_line=True)._parsedata(s, pos)
# select a literal string exactly
FIND_SELECTION = p.Keyword('FIND', caseless=True).suppress() - STRING_MATCH_EXPRESSION
@FIND_SELECTION.set_parse_action
def parse_find_selection(s, pos, tokens):
    return n.FindSelection(tokens[0])._parsedata(s, pos)
# select a large block from two other selections
BLOCK_SELECTION = p.Keyword('FROM', caseless=True).suppress() - CURSOR_OR_SELECTION - p.Keyword('TO', caseless=True).suppress() - CURSOR_OR_SELECTION
@BLOCK_SELECTION.set_parse_action
def parse_block_selection(s, pos, tokens):
    return n.BlockSelection(*tokens)._parsedata(s, pos)
# select a large block between two other selections
BETWEEN_SELECTION = p.Keyword('BETWEEN', caseless=True).suppress() - CURSOR_OR_SELECTION - p.Keyword('AND', caseless=True).suppress() - CURSOR_OR_SELECTION
@BETWEEN_SELECTION.set_parse_action
def parse_between_selection(s, pos, tokens):
    return n.BlockSelection(*tokens, inclusive=False)._parsedata(s, pos)
# select a portion of a previous selection
SUB_SELECTION = SELECTION - p.Keyword('OF', caseless=True) - SELECTION
@SUB_SELECTION.set_parse_action
def parse_sub_selection(s, pos, tokens):
    return n.SubSelection(*tokens)._parsedata(s, pos)
# if a selection has multiple matches, select the nth one
RANGE_INDEX_SELECTION = RANGE_INDEX_LIST - SELECTION
@RANGE_INDEX_CURSOR.set_parse_action
def parse_range_index_selection(s, pos, tokens):
    return n.RangeIndexSelection(*tokens)._parsedata(s, pos)
SELECTION <<= DIRECT_LINE_SELECTION | FIND_LINE_WITH_SELECTION | FIND_SELECTION | FIND_LINE_SELECTION | BLOCK_SELECTION | SUB_SELECTION | RANGE_INDEX_SELECTION
