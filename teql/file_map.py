from bisect import bisect
from typing import Tuple,Iterable

class FileMap:
    """
    This class stores line metadata for a file, making it easy to translate cursor locations to 
    line and column numbers.

    This is intended to work on byte strings rather than unicode strings.
    """
    def __init__(self, linebreaks:Iterable[int], filesize:int):
        """
        Initialize the map from a list of linebreak cursor positions. This will be a list of cursor
        positions immediately after each linebreak character
        """
        self.linebreaks = tuple(linebreaks)
        self.filesize = filesize
        self.eol_size = 1 # TODO calculate or pass as parameter?
    
    @classmethod
    def from_lines(cls, lines:Iterable[bytes]):
        cursor = 0
        breaks = []
        for line in lines:
            cursor += len(line)
            if line[-1] in b'\r\n':
                breaks.append(cursor)
        return cls(breaks, cursor)

    def cursor_to_line(self, cursor:int)->int:
        """
        Given a cursor somewhere in the file, return the line number that cursor appears on.

        A cursor after a line break will be considered as falling on the following line.
        """
        lineno = bisect(self.linebreaks, cursor)
        # +1 because we index lines starting with 1
        return lineno+1
    
    def cursor_to_line_col(self, cursor:int)->Tuple[int,int]:
        """
        Given a cursor somewhere in the file, return the line and column of the byte 
        immediately following the cursor.

        Note that cursors conceptually exist between byte, but you can think of this as the 
        line an column where a character would be located if inserted at this cursor.

        If you are using a multi-byte character encoding for the file, there is no guarantee that 
        the returned line and column are not in the middle of character.
        """
        lineno = bisect(self.linebreaks, cursor)
        if lineno == 0:
            # Line 0 always starts at cursor position 0, so is not in the line break map
            colno = cursor
        else:
            # colno is cursor minus end position of previous line
            colno = cursor - self.linebreaks[lineno-1]
        # +1 because we index lines/columns starting with 1
        return lineno+1, colno+1
    
    def line_to_cursor(self, lineno:int)->int:
        """
        Given a line number, return the cursor position at the beginning of the line
        """
        # -1 because we index lines/columns starting with 1
        # -1 again because line 1 always starts at cursor position 0, so is not in the line break map
        lineno -= 2
        if lineno < 0:
            return 0
        return self.linebreaks[lineno]
        
    def line_to_start_end_cursor(self, lineno:int)->Tuple[int,int]:
        """
        Return both the cursor position at the beginning of the given line, and the cursor 
        position at the end (after the line's EOL character, if present).
        """
        # -1 because we index lines/columns starting with 1
        lineno -= 1
        if lineno == len(self.linebreaks):
            # Cursor is after last linebreak
            end_cursor = self.filesize
        else:
            end_cursor = self.linebreaks[lineno]
        if lineno == 0:
            return (0,end_cursor)
        else:
            # -1 again because line 1 always starts at cursor position 0, so is not in the line break map
            start_cursor = self.linebreaks[lineno-1]
            return (start_cursor,end_cursor)

    def line_length(self, lineno:int)->int:
        """
        Return the length (in bytes) of the given line
        """
        start, end = self.line_to_start_end_cursor(lineno)
        return end - start
    
    def line_col_to_cursor(self, lineno:int, colno:int)->int:
        """
        Given a line and column, return the cursor position immediately before that line and 
        column. A byte inserted at this cursor position would be placed in the given row and column.

        If you are using a multi-byte character encoding for the file, there is no guarantee that 
        the returned cursor is not in the middle of character.
        """
        start, end = self.line_to_start_end_cursor(lineno)
        # -1 because we index columns at 1 instead of 0
        return min(start + colno - 1, end)
    