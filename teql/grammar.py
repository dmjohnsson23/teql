import pyparsing as p
import parse_nodes as n
from ast import literal_eval

COMMENT = p.Suppress((p.Literal('--') - p.rest_of_line) | (p.Literal('//') - p.rest_of_line) | p.Literal('/*') + p.NotAny('*') - p.SkipTo(p.Literal('*/')) - p.Literal('*/'))

LITERAL_STRING = p.python_quoted_string
@LITERAL_STRING.set_parse_action
def parse_literal_string(s, pos, tokens):
    # Hijack python's string parsing
    return n.LiteralString(literal_eval(tokens[0]))._parsedata(s, pos)
LITERAL_REGEX = p.QuotedString('/', '\\')
@LITERAL_REGEX.set_parse_action
def parse_literal_regex(s, pos, tokens):
    return n.LiteralRegex(tokens[0])._parsedata(s, pos)
LITERAL_INT = (p.Suppress('0x') + p.common.hex_integer) | (p.Suppress('0b') + p.Word('10').set_parse_action(lambda bits: int(bits, base=2))) | p.common.signed_integer
@LITERAL_INT.set_parse_action
def parse_literal_int(s, pos, tokens):
    return n.LiteralInt(tokens[0])._parsedata(s, pos)
LITERAL_FLOAT = p.common.fnumber
@LITERAL_FLOAT.set_parse_action
def parse_literal_float(s, pos, tokens):
    return n.LiteralFloat(tokens[0])._parsedata(s, pos)

CURSOR = p.Forward()
SELECTION = p.Forward()
CURSOR_OR_SELECTION = CURSOR | SELECTION
RANGE_INDEX = p.delimited_list(p.Keyword('FIRST', caseless=True) - p.Opt(LITERAL_INT) | p.Keyword('NEXT', caseless=True) - p.Opt(LITERAL_INT)  | p.Keyword('LAST', caseless=True) - p.Opt(LITERAL_INT)  | (LITERAL_INT - p.Literal(':') - LITERAL_INT) | LITERAL_INT)

# place cursor at the start of the current context
START_CURSOR = p.Keyword('START', caseless=True)
# place cursor at the end of the current context
END_CURSOR = p.Keyword('END', caseless=True)
# place cursor at the after a selection or cursor
SELECTION_AFTER_CURSOR = p.Keyword('AFTER', caseless=True) - CURSOR_OR_SELECTION
# place cursor before a selection or cursor
SELECTION_BEFORE_CURSOR = p.Keyword('BEFORE', caseless=True) - CURSOR_OR_SELECTION
# place a cursor in the context of a selection
SELECTION_CURSOR = CURSOR - p.Keyword('OF', caseless=True) - SELECTION
# if a cursor has multiple matches, select the nth one
RANGE_INDEX_CURSOR = RANGE_INDEX - CURSOR
CURSOR <<= START_CURSOR | END_CURSOR | SELECTION_AFTER_CURSOR | SELECTION_BEFORE_CURSOR | SELECTION_CURSOR | RANGE_INDEX_CURSOR

# select a specific line by line number; negative to select from end
DIRECT_LINE_SELECTION = p.Keyword('LINE', caseless=True) - LITERAL_INT
# select a line containing a literal strings
LINE_WITH_SELECTION = p.Keyword('LINE', caseless=True) - p.Keyword('WITH', caseless=True) - LITERAL_STRING
# select a literal string exactly
FIND_SELECTION = p.Keyword('FIND', caseless=True) - LITERAL_STRING
# select a line matching literal string
FIND_LINE_SELECTION = p.Keyword('FIND', caseless=True) - p.Keyword('LINE', caseless=True) - LITERAL_STRING
# select a large block from two other selections
BLOCK_SELECTION = p.Keyword('FROM', caseless=True) - CURSOR_OR_SELECTION - p.Keyword('TO', caseless=True) - CURSOR_OR_SELECTION
# select a portion of a previous selection
SUB_SELECTION = SELECTION - p.Keyword('OF', caseless=True) - SELECTION
# if a selection has multiple matches, select the nth one
RANGE_INDEX_SELECTION = RANGE_INDEX - SELECTION
SELECTION <<= DIRECT_LINE_SELECTION | LINE_WITH_SELECTION | FIND_SELECTION | FIND_LINE_SELECTION | BLOCK_SELECTION | SUB_SELECTION | RANGE_INDEX_SELECTION
