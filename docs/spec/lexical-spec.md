# Lexical Specification

## Token Classes

VECTIS tokens are categorized as follows:

- **Keyword**
- **Identifier**
- **String Literal**
- **Numeric Literal**
- **Comment**
- **Whitespace**
- **Punctuation**
- **Operator**

## Reserved Keywords

The following keywords are reserved and cannot be used as identifiers:

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

## Identifiers

Identifiers are used to name variables, functions, and other entities. They must:

- Start with a letter (a-z, A-Z) or underscore (_)
- Contain only letters, digits (0-9), and underscores
- Be case-sensitive

Examples:

- `accessible_tools`
- `user_input`
- `data_analysis`

Invalid examples:

- `123tools` (starts with a digit)
- `user-input` (contains hyphen)
- `user input` (contains space)

## String Literals

String literals are enclosed in double quotes (`"`). They may contain any character except the closing quote, and may span multiple lines.

Examples:

- "accessible developer tools"
- "This is a multi-line
string literal."

Invalid examples:

- "unterminated string
- "escaped "quote"

## Numeric Literals

Numeric literals can be integers or floating-point numbers. They may include an optional leading sign (`+` or `-`), and may use underscores as separators for readability.

Examples:

- `42`
- `3.14`
- `+100_000`
- `-0.001`

Invalid examples:

- `123_456` (valid in some contexts, but not in VECTIS)
- `123.45.67` (invalid format)
- `123_45_67` (invalid format)

## Comments

Single-line comments start with `//` and extend to the end of the line.

Examples:

- `// This is a comment`
- `// A single-line comment`

Invalid examples:

- `// This is an invalid comment` (valid, but not an example of invalid syntax)
- `// This is a comment with a line break
// This is a second line`

## Whitespace

Whitespace characters (spaces, tabs, newlines) are generally ignored except within string literals and comments. Multiple whitespace characters are treated as a single space.

Examples:

- `  // This is a comment with leading whitespace`
- `  // This is a comment with multiple spaces`

Invalid examples:

- `  // This is a comment with leading whitespace` (valid, but not an example of invalid syntax)
- `  // This is a comment with multiple spaces` (valid, but not an example of invalid syntax)

## Punctuation

Punctuation characters are used to delimit tokens and include:

- `{` and `}` (block delimiters)
- `(` and `)` (parentheses)
- `[` and `]` (brackets)
- `;` (statement separator)
- `,` (comma)

## Operators

Operators are used to perform operations and include:

- `>=` (greater than or equal to)
- `<=` (less than or equal to)
- `==` (equal to)
- `!=` (not equal to)
- `+` (addition)
- `-` (subtraction)
- `*` (multiplication)
- `/` (division)
- `&&` (logical AND)
- `||` (logical OR)
- `!` (logical NOT)

## Source Span Behavior

Each token includes source span information that indicates its position in the source file. This information is used for diagnostics and error reporting.

## Valid and Invalid Examples

Valid examples:

```vectis
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
```

Invalid examples:

```vectis
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
```

Note: The invalid example is identical to the valid example, but the intention is to demonstrate that the invalid example is not syntactically correct. In practice, the invalid example would be a valid example, and the valid example would be an invalid example.