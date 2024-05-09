# Text Editor Query Language

Idea for an SQL-inspired language to perform bulk edits to text files. This is designed as a more verbose but easier to learn combination of `sed` and `grep`. You would be able to explore and edit a file or set of files from an interactive shell, or run simple queries directly from your system shell.

```
teql> USE 'somefile.txt';
teql> SET linenumbers = on;
teql> SHOW FIND LINE WITH 'grep';
6  Hey, this is kinda like grep!;
11 Like grep, we'll print out any lines matching the selector
teql> REPLACE "grep" IN LINE 6 WITH "sed";
teql> SHOW LINE 6;
6  Hey, this is kinda like sed!;
teql> DELETE EVERYTHING AFTER FIND FIRST LINE LIKE "The End";
```

## Rational

I find myself doing a great deal of refactoring. Often this is dull and boring, with repeated use of find-and-replace across multiple files. However, using find-and-replace has some difficulties:

1. Sometimes is is necessary to find-and-replace two sections in the same file at the same time, ensuring both sections are matched and replaced in a single "transaction"
2. Sometimes I want to change one line based on the content of another line elsewhere in the file (e.g. change this parameter in files which also contain this if statement)
3. Composing regexes to match properly can sometimes be annoying (especially in regards to whitespace differences)
4. Preserving indentation when inserting lines can be challenging and messy

Additionally, I occasionally need to edit files which are too large to be opened in a text editor. An editing language like this provides a way to make changes to files without loading them into memory. (I'm not targeting "single pass" editing like sed though)

## Existing Solutions

There are already some script-based file editing tools. 

* `sed`: Frankly `sed` is difficult to learn, difficult to use, uses difficult to read scripts, is rather inflexible.
* Perl: The programming language is designed around text processing, but it's frankly too powerful for the fairly simple tasks I want to do, I'd like something simpler where I can just throw together a quick query to do what I want and move on, rather than writing a program to do it.

## Proposed Syntax

SQL is a great language for making bulk change to a database. Why not use something similar to make bulk changes to text files? For example:

```
UPDATE */rep_current.php
CHANGE "Auth::protectPageOrDie();" TO "Auth::protectPageOrDie(UserLevel::READ_ONLY);"
WHERE ANY LINE = '<?php if ($_SESSION['level'] >= UserLevel::READ_ONLY) { ?>'
```

### Query Types

I see value in the following types of queries to TEQL:

* `SELECT...FROM`: A simple search feature
* `UPDATE`: Actually perform updates to the file
* `PREVIEW UPDATE`: The same as update, but write to stdout instead of overwriting the file
* `CREATE...FROM`: Create a new file based on the specified file
* `CREATE DIFF...FROM`: Create a diff file for the changes that would be applied
* `SET` Set a global variable or session setting
* `USE` Set the default file to use for all queries, to avoid specifying it each time.

### Search operations

WIP Section

Still working out how to work with getting data from file contents versus the file itself. This doesn't translate perfectly to a nice flat "table"

Searching uses a `SELECT...FROM` syntax like SQL. Whatever is between `SELECT` and `FROM` indicates what data about the matched files or lines you would like returned.

We could select the following types of data:

* The name of all matched files
* The actual matched lines
* Number of matches found

I envision something like this:

```
SELECT file_name
FROM *.php
WHERE FILE CONTAINS "search string"
```

The idea would be to allow asking questions like this about a codebase:

* Is this code duplicated elsewhere in the project?
* Which files contain this search key but not this other one?
* How many times does this key appear in each file?
* How many lines of code are in the project?
* Where is this deprecated functionality used?
* Where is this or that bad programming practice used? (e.g. search for syntax patterns you want to get rid of)

### Editing operations

These would be supported on all query types except `SELECT`.

* `INSERT...[BEFORE|AFTER|AT]`
* `CHANGE...TO`
* `DELETE`
* `DELETE...[BEFORE|AFTER|AT]`
* `INDENT [amount]`

#### INSERT

Insert based on line number: (The second `LINE` keyword can be optional and is implied if omitted)

```
UPDATE somefile
INSERT LINE "This line will be inserted" AT LINE 5
```

Negative numbers supported (to insert n lines from the end)

```
UPDATE somefile
INSERT LINE "This line will be inserted" AT LINE -5
```

Insert a line at the beginning or end of the file (The `FILE` keyword is optional and implied if ommitted):

```
UPDATE somefile
INSERT LINE "This line will be inserted" AT FILE END
```

Insert based on a matched line:

```
UPDATE somefile
INSERT LINE "This new line will be inserted" BEFORE "This line already exists"
```

Combined form to insert relative to a matched line:

```
UPDATE somefile
INSERT LINE "This new line will be inserted" AT 3 AFTER "This line already exists"
```

If the first `LINE` keyword is omitted, the behavior changes. Now it will insert values in place on the existing line:

```
UPDATE somefile
INSERT "This will be added to the end of line 5" AT LINE 5 END
```

```
UPDATE somefile
INSERT " add this mid-line " BEFORE "existing part of line"
```

#### CHANGE...TO

Make a change to matched text.

Change a literal value anywhere in the file:

```
UPDATE somefile
CHANGE "thisname" TO "othername"
```

Replace an entire line (not considering leading and trailing whitespace):

```
UPDATE somefile
CHANGE LINE "return this;" TO "return something_else;"
```

#### DELETE

Delete only the matched text:

```
UPDATE somefile
DELETE "delete me"
```

Using a regex or `LIKE` operation to delete parts of a line:

```
UPDATE somefile
DELETE LIKE "// TODO%"
```

Delete an entire line:

```
UPDATE somefile
DELETE LINE "delete this line"
```

#### INDENT

Change the indentation of a line or lines:

Values are in "units of indentation" which, could be 1 tab, 4 spaces, 2 spaces; whatever is configured in the tool, or possibly detected from the file. The value can be a positive delta, negative delta, or an absolute value.

```
UPDATE somefile
INDENT -1 LINE 'Remove 1 unit of indentation from this line'
INDENT +1 LINE 'Add 1 unit of indentation from this line'
INDENT 0 LINE "Set this line's indentation to 0"
```

#### Chained editing operations

Operations in a single query will all be performed against the same base version of the file, rather than as subsequent operations.

For example, in this example file:

```
thisname
othername
```

With this code:

```
UPDATE somefile
CHANGE "thisname" TO "othername"
CHANGE "othername" TO "newname";
```

The resulting file would be:

```
othername
newname
```

However, this code:

```
UPDATE somefile
CHANGE "thisname" TO "othername";

UPDATE somefile
CHANGE "othername" TO "newname";
```

Would result in:

```
newname
newname
```


### More complex selection criteria

Select only the first or last matching lines:

```
UPDATE somefile
DELETE LAST LINE LIKE "return%"
```

index into the matched lines: (below deletes the 4th and 6th lines starting with 'return')

```
UPDATE somefile
DELETE 4,6 LINE LIKE "return%"
```

Select a block based on start and end lines (both matched lines must have the same indentation):

```
UPDATE somefile
DELETE FROM LINE "if (condition){" TO LINE "}"
```

Or a non-greedy version of the above:

```
UPDATE somefile
DELETE FROM LINE "if (condition){" TO NEXT LINE "}"
```

And a version that does not require the same indentation:

```
UPDATE somefile
DELETE FROM LINE "if (condition){" TO ANY NEXT LINE "}"
```

Also a block selection that matches the contents, but not the start and end match themselves:

```
UPDATE somefile
DELETE BETWEEN LINE "if (condition){" TO LINE "}"
```

We can match en entire line based on only a portion of the line using `LINE WITH`. This differs from just omitting the `LINE` keyword altogether as if will still select the entire line, not just the matched text.

```
UPDATE somefile
DELETE LINE WITH "return"
```

Other matching criteria to support (Not sure on syntax yet...)
* Match a line if and only if it is followed/preceded by a different match
* Match a contiguous block of matches as a single matched section (e.g. find a block of lines that each individually match a pattern)

### WHERE clauses

A WHERE clause can be applied both to the files, and to the individual operations performed thereon.

Filter files to only those with matching criteria for all operations:

```
UPDATE *.php
WHERE FILE CONTAINS LINE "search the file for this line"
CHANGE "some value" TO "another value"
```

Conditionally perform the individual operation:

```
UPDATE *.php
CHANGE "some value" TO "another value"
WHERE LINE CONTAINS "search the line"
```

### Matching Files

Where the file is specifed in the query, a file glob pattern is accepted by default, or a list of files. It may optionally be surrounded by quotes if needed.

```
UPDATE /path/to/file/*.html
...
```

```
UPDATE file1.py file2.py file3.py
...
```

```
UPDATE "/this/path has/whitespace.txt"
...
```

```
UPDATE "/also/allow/{bash|shell}/expansion.txt"
...
```

If desired, you can instead use regex or a `LIKE` operator (The `FILES` keyword here is optional):

```
UPDATE FILES REGEXP "[_a-z]+\.php"
...
```

```
UPDATE FILES LIKE "%.html"
...
```


### Matching Lines

Match a literal string somewhere in the line:

```
UPDATE somefile
INSERT LINE "some line" BEFORE "some part of the line"
```

Matching the entire line (not considering leading or trailing whitespace):

```
UPDATE somefile
INSERT LINE "some line" BEFORE LINE "Match this entire line"
```

Matching the entire line (including leading and trailing whitepace):

```
UPDATE somefile
INSERT LINE "some line" BEFORE FULL LINE "    Match this entire line"
```

You can also use regex or the `LIKE` operator:

```
UPDATE somefile
INSERT LINE "some line" BEFORE LINE REGEXP '^[a-zA-Z0-9_]+\s*=\s*.*;$'
```

```
UPDATE somefile
INSERT LINE "some line" BEFORE LINE LIKE '%=%'
```

We can also match multiple lines (Any indentation here will be relative to the first non-empty line's indentation):
```
UPDATE somefile
INSERT LINE "some line" BEFORE LINES """
first line
second line
"""
```

### Aliases

We can find and alias matches for use in multiple operations:

```
UPDATE somefile
USE LINES """
result = doThing();
doOtherThing(result);
""" AS the_block
INSERT LINE "if (condition){" BEFORE the_block
INSERT LINE "}" AFTER the_block
INDENT +1 the_block
```

### Session Settings

The following session settings can be configured using a `SET` query:

* encoding: The encoding to use when reading and writing files. Defaults to the system's default encoding. (This is *not* the encoding of the TEQL script itself)
* linesep: The line separator to use when reading and writing files. Defaults to the system's default line separator.
* linenumbers: If set to `on`, line numbers will be displayed when printing to sdtout.

### String interpolation

Like in bash or PHP, double-quoted strings will be interpolated. The `$` will indicate a value to be replaced. This can be used to get matched values from the line, regex capture groups, or special values like the file name.

```
UPDATE somefile
CHANGE LINE REGEXP '^old_prefix_([a-zA-Z0-9_]+)\s*=\s*(.*);$' TO "new_prefix_$1 = $2"
```

The more complex format `${}` will allow performing operations on the interpolated value, e.g. `${filename | replace_pattern '\.[a-zA-Z0-9]+%' '' | replace '_' ' ' | capitalize}`

### Arrays

Arrays are 1-indexed like in SQL, and as is usually expected with numbering the lines of a file. Index 0 exists, but is a special-purpose index. For example, in regex matches, index 0 is the whole match, while the normally-numbered indices are the individual capture groups.

## TODOs

* Ideally I think we can accomplish this in a single pass for SELECT operations, and two passes for UPDATE operations (one to decide what to do, and one to do it), but right now I'm just focused on making things actually *function*.
* Python may not be the best language choice, since the goal is to have an efficient way of doing complex batch updates to multiple files (and potentially include it in IDEs!). Right now I'm mostly just prototyping in a "comfortable" language. Might be a good opportunity for me to get proficient with Rust when I rewrite; seems like that would be a better language choice.
* Because of how parsing is handled, LITERAL_PATH must be followed by a space before you can use a semicolon to end the query. This is annoying and confusing.

* Path arguments to queries should be optional; we can USE the file or apply an optional USING argument
* UPDATE should be split into several different query types instead of being in one umbrella, and we can instead use transactions to perform all updates simultaneously

Also need to figure out exactly how the values/variable stores work. I could see us having up to three-dimensional values: a SELECT query with multiple selectors, each having potentially multiple matches, executed against multiple files. The "matches" dimension is probably the most problematic, as it would not even be guaranteed to be the same size for all selectors/files. We also need a nice way to "collapse" flat dimensions, like SQL does. I'd also like to have some sort of property access, e.g. for accessing match groups on a regex or other metadata like that. If we could constrain it to two dimensions some how, we could maybe use pandas as a data store.

Ultimately, I think `SELECT` is conceptually too complicated. A `FIND` or `SEARCH` might be a better option, which just looks for matches but doesn't try to distinguish where they came from (Similar to `grep`). (That data could be included in the metadata though.) Perhaps a simplified `SELECT` more similar to `awk` could be created?