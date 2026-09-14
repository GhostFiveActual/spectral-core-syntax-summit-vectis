# VECTIS Lexical Specification

This document defines the normative lexical rules for VECTIS source text.
The lexer must follow these rules exactly. Examples marked invalid are
intentionally invalid and must not be interpreted as alternate syntax.

## 1. Token Classes

VECTIS source may produce the following token classes:

- Keyword
- Identifier
- String Literal
- Numeric Literal
- Comment
- Punctuation
- Operator

Whitespace separates tokens but is not emitted as a semantic token by the
reference lexer. Comments may be recognized by the lexer but may be omitted
from the parser token stream.

Every emitted token must retain an exact source span.

## 2. Reserved Keywords

The following words are reserved:

- `mission`
- `source`
- `analyze`
- `when`
- `otherwise`
- `publish`
- `request`
- `require`
- `citations`
- `confidence`
- `report`
- `review`

Reserved keywords cannot be used as identifiers.

Keyword matching is case-sensitive.

Examples:

~~vectis
mission
source
when
publish
~~

These are identifiers, not keywords:

~~vectis
Mission
source_data
publish_result
~~

## 3. Identifiers

An identifier:

1. begins with an ASCII letter (`A-Z` or `a-z`) or underscore (`_`);
2. continues with zero or more ASCII letters, digits (`0-9`), or underscores;
3. is case-sensitive;
4. must not exactly match a reserved keyword.

Valid identifiers:

~~text
accessible_tools
user_input
_data2
Report
~~

Invalid identifiers:

~~text
123tools
user-input
user input
~~

The first invalid form begins with a digit. The second contains a hyphen,
which is tokenized separately. The third contains whitespace and therefore
represents two identifiers rather than one identifier.

## 4. String Literals

String literals begin and end with a double quote (`"`).

A string may contain ordinary characters and newline characters. A raw
unescaped double quote terminates the string.

Escape sequences are not defined in the current lexical version. A future
language revision may introduce them explicitly.

Valid:

~~vectis
"accessible developer tools"
"first line
second line"
""
~~

Invalid:

~~text
"unterminated string
~~

An unterminated string is a lexical error and must produce a diagnostic with
its source location.

## 5. Numeric Literals

Numeric literals support:

- unsigned integers;
- signed integers;
- unsigned decimal numbers;
- signed decimal numbers.

A leading `+` or `-` is part of the numeric literal only when immediately
followed by a digit.

Digits may not contain underscore separators in the current lexical version.

Valid:

~~text
42
+42
-42
3.14
+0.5
-0.001
~~

Invalid numeric forms:

~~text
123_456
1_000
123.45.67
.
+.
-.
~~

`123_456` is not a valid numeric literal. Depending on surrounding syntax,
a conforming lexer may tokenize it as a numeric token followed by an
identifier beginning with underscore, or report it as malformed input if
the implementation validates contiguous numeric-looking sequences. It must
not silently treat the underscore as a numeric separator.

## 6. Comments

A single-line comment begins with `//` and extends through the final
character before the next newline or end-of-file.

Examples:

~~vectis
// This is a comment
mission "demo" { // trailing comment
}
~~

A newline terminates the comment. A second line beginning with `//` is a
separate comment.

VECTIS does not currently define block comments.

## 7. Whitespace

The following characters are lexical whitespace outside strings:

- space
- horizontal tab
- carriage return
- newline

Whitespace separates tokens where necessary and is otherwise ignored.

Whitespace still affects source-position tracking. Line and column
information must advance through ignored whitespace exactly as it does
through emitted tokens.

## 8. Punctuation

The current punctuation tokens are:

- `{`
- `}`
- `(`
- `)`
- `[`
- `]`
- `;`
- `,`

Each punctuation symbol is a distinct token.

## 9. Operators

The current operators are:

- `>=`
- `<=`
- `==`
- `!=`
- `+`
- `-`
- `*`
- `/`
- `&&`
- `||`
- `!`

For operators with shared prefixes, longest-match behavior is required.

Examples:

- `>=` must be emitted as one operator token.
- `!=` must be emitted as one operator token.
- `!` remains valid as a single operator.
- `/` is an operator unless followed immediately by `/`, which begins a
  comment.

Bare `<`, bare `>`, bare `=`, bare `&`, and bare `|` are not operators in
the current language version and must produce lexical diagnostics.

## 10. Source Position and Span Rules

Source locations use the canonical compiler models:

- `SourcePosition`
- `SourceSpan`
- `Token`

Lines and columns are 1-based.

The first character of a source file is:

~~text
line = 1
column = 1
~~

Every emitted token must contain a `SourceSpan` whose start and end positions
refer to the same source file.

Implementations must advance source positions through:

- emitted tokens;
- ignored whitespace;
- comments;
- newline characters;
- multiline strings.

The lexer must never hard-code token locations.

## 11. Lexical Errors

The lexer must reject malformed lexical input with a useful diagnostic.

At minimum, diagnostics are required for:

- unterminated string literals;
- unsupported bare operator prefixes such as `<`, `>`, `=`, `&`, and `|`;
- otherwise unrecognized characters.

A lexical diagnostic must identify the offending source location.

## 12. Representative Valid Program

~~vectis
mission "Research accessibility tools" {
    source web {
        query "accessible developer tools"
    }

    analyze findings {
        require citations
    }

    when confidence >= 0.80 {
        publish report
    }

    otherwise {
        request review
    }
}
~~

This example is intended primarily to demonstrate lexical forms. Later
parser and semantic specifications determine whether every identifier and
construct is grammatically and semantically valid.

## 13. Representative Invalid Lexical Inputs

Unterminated string:

~~text
mission "Research accessibility tools
~~

Unsupported bare comparison operator:

~~text
when confidence > 0.80
~~

Unsupported single ampersand:

~~text
left & right
~~

Malformed numeric-looking sequence:

~~text
confidence 1.2.3
~~

These examples are intentionally invalid and are distinct from the valid
example above.

## 14. Reference Lexer Conformance

A conforming lexer implementation must demonstrate tests for:

1. reserved keywords;
2. identifiers;
3. strings, including multiline and empty strings;
4. integers and decimals;
5. optional numeric signs;
6. rejection or non-numeric treatment of underscore-separated numbers;
7. `//` comments;
8. whitespace handling;
9. all punctuation;
10. all operators;
11. longest-match operators;
12. unsupported bare operator prefixes;
13. invalid characters;
14. unterminated strings;
15. correct line and column progression;
16. source spans across multiline input.
