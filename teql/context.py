from functools import reduce
import re
import io
from mmap import mmap
import sys, os
from operator import or_
from typing import List


class Context:
    data: mmap
    start: int
    start_line:int = None # Line number of first selected line
    end: int
    end_line:int = None # Line number of last selected line
    encoding: str
    line_separator: bytes
    parent: 'Context'
    match_data: re.Match
    highlights: List['Context'] # Any sub-selections which should be highlighted (e.g. the matched term in a selected line)

    def __init__(self, data, start=None, end=None, *, encoding=None, line_separator=None, parent=None, _match_data=None):
        """
        
        """
        self.start = start
        self.end = end
        self.encoding = encoding or sys.getdefaultencoding()
        self.line_separator = line_separator or os.linesep
        if isinstance(self.line_separator, str):
            self.line_separator = self.line_separator.encode(self.encoding)
        self.parent = parent
        self.match_data = _match_data
        if isinstance(data, Context):
            # Sub-selection
            self.parent = data
            self.data = data.data
            self.start += data.start
            self.end += data.start
            self.encoding = data.encoding
            if self.end > data.end:
                raise Exception('Sub-selection out of bounds')
        elif isinstance(data, mmap):
            self.data = data
        elif isinstance(data, io.IOBase):
            try:
                self.data = mmap(data.fileno(), 0)
            except io.UnsupportedOperation:
                # Probably not a "real" file, so try to copy into an mmap
                if isinstance(data, io.BytesIO):
                    data.seek(0, os.SEEK_END)
                    self.data = mmap(-1, data.tell())
                    data.seek(0)
                    while True:
                        page = data.read(1024)
                        if not page:
                            break
                        self.data.write(page)
                elif isinstance(data, io.TextIOBase):
                    data.seek(0, os.SEEK_END)
                    self.data = mmap(-1, data.tell()) # FIXME assumes single-byte encoding
                    data.seek(0)
                    while True:
                        page = data.read(1024)
                        if not page:
                            break
                        self.data.write(page.encode(self.encoding))
        elif isinstance(data, (bytes,bytearray)):
            self.data = mmap(-1, len(data))
            self.data.write(data)
        elif isinstance(data, str):
            data = data.encode(self.encoding)
            self.data = mmap(-1, len(data))
            self.data.write(data)
        if self.start is None:
            self.start = 0
        if self.end is None:
            self.data.seek(0, os.SEEK_END)
            self.end = self.data.tell()
    
    def find(self, value):
        """
        Get a new context by searching this context for a matching string
        """
        if isinstance(value, str):
            value = value.encode(self.encoding)
        index = self.data.find(value, self.start, self.end)
        if index == -1:
            return None
        return Context(self.data, index, index+len(value), encoding=self.encoding, parent=self)
    
    def find_all(self, value):
        """
        Get new contexts by searching this context for matching strings
        """
        if isinstance(value, str):
            value = value.encode(self.encoding)
        start = self.start
        while start < self.end:
            index = self.data.find(value, start, self.end)
            if index == -1:
                break
            start = index + len(value)
            yield Context(self.data, index, start, encoding=self.encoding, parent=self)
    
    def find_re(self, value, flags=None):
        """
        Get a new context by searching this context using a regular expression
        """
        if isinstance(value, str):
            value = value.encode(self.encoding)
        pattern = re.compile(value, _interpret_flags(flags))
        matched = pattern.search(self.data, self.start, self.end)
        if not matched:
            return None
        return Context(self.data, matched.pos, matched.endpos, encoding=self.encoding, parent=self, _match_data = matched)
    
    def find_all_re(self, value, flags=None):
        """
        Get new contexts by searching this context using a regular expression
        """
        if isinstance(value, str):
            value = value.encode(self.encoding)
        pattern = re.compile(value, _interpret_flags(flags))
        for matched in pattern.finditer(self.data, self.start, self.end):
            yield Context(self.data, matched.start(), matched.end(), encoding=self.encoding, parent=self, _match_data = matched)
    
    def sub(self, start, end):
        """
        Get a sub-selection (A selection with start/end points relative to this selection)
        """
        return Context(self, start, end)
    
    def file(self):
        """
        Expand the context selection to the entire file
        """
        return Context(self.data, encoding=self.encoding, line_separator=self.line_separator)
    
    def bytes(self, start=None, end=None):
        """
        Return the raw unencoded bytes between the two indices
        """
        if start is None:
            start = self.start
        elif start < 0:
            start = self.end + start
        else:
            start = self.start + start
        if end is None:
            end = self.end
        elif end < 0:
            end = self.end + end
        else:
            end = self.start + end
        if end > self.end:
            raise IndexError()
        return self.data[start:end]
    
    def string(self, start=None, end=None):
        """
        Return an encoded string (or substring).
        """
        return self.bytes(start, end).decode(self.encoding)
    
    def expand_to_lines(self):
        """
        Expand the selection to include only full lines (no partial lines).
        """
        # TODO it may be good to keep an array of line start indices, and use the standard bisect module to search it, enabling fast line number lookups
        len_eol = len(self.line_separator)
        size = self.data.tell()
        if self.start == 0:
            start = 0
        else:
            # Track backward to previous EOL
            prev_eol = self.data.rfind(self.line_separator, 0, self.start)
            if prev_eol == -1:
                # Failed to find any prior EOL; go to the beginning of the file
                start = 0
            else:
                start = prev_eol + len_eol
        self.data.seek(0, os.SEEK_END)
        if self.end == size:
            end = self.end
        else:
            # Track forward to the next EOL, unless the selection already ends with EOL
            end = self.data.find(self.line_separator, max(0, self.end - len_eol))
            if end == -1:
                # Failed to find any subsequent EOL; go to the end of the file
                end = prev_eol + len_eol
            else:
                # Include the line ending in the result
                end += len_eol
        return Context(self.data, start, end, encoding=self.encoding, line_separator=self.line_separator)

    def split_lines(self):
        """
        Split the context into multiple lines of context
        """
        value = self.line_separator
        start = self.start
        while start < self.end:
            index = self.data.find(value, start, self.end)
            if index == -1:
                break
            end = index + len(value)
            yield Context(self.data, start, end, encoding=self.encoding, parent=self)
            start = end
    
    def __len__(self):
        return self.end - self.start
    
    def __repr__(self):
        if self.start == self.end:
            return f"Cursor @ {self.start}"
        if len(self) < 60:
            string = repr(self.string())
        else:
            string = f"{repr(self.string(0, 29))}...{repr(self.string(-28))}"
        return f"Selection @ {self.start}-{self.end}: {string}"


def _interpret_flags(flags):
    if flags is None:
        return 0
    if isinstance(flags, str):
        return reduce(or_, map(lambda f: {
            'i': re.I,
            'l': re.L,
            'm': re.M,
            's': re.S,
            'u': re.U,
            'x': re.X,
        }[f], flags.lower()), 0)
    if isinstance(flags, int):
        return flags
    raise ValueError("Unknown flags: {}")