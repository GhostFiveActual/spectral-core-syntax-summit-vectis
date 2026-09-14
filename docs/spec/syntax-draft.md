# Syntax Draft

Status: historical and non-normative.

This document is retained as an early language-design artifact. It does not
define current VECTIS syntax and must not be used to implement or validate the
parser.

The authoritative concrete grammar is `docs/spec/grammar.md`. The normative
lexical contract is `docs/spec/lexical-spec.md`.

## Historical Draft Content

Status: normative and definitive.

## Grammar Overview

VECTIS is a deterministic domain-specific language with the following core constructs:

### Top-Level Constructs

- `mission` - Defines a mission with a name and body
- `source` - Specifies data sources
- `analyze` - Defines analysis steps
- `when` - Conditional execution
- `otherwise` - Default case

### Blocks

Blocks are defined using `{` and `}` and contain a sequence of statements. Blocks can contain:
- Expressions
- Literals
- Lists
- Conditionals

### Expressions

Expressions are evaluated to produce a value. They can include:
- Literals
- Operators
- Function calls
- Parenthesized expressions

### Lists and Literals

- Lists are defined using square brackets `[]`
- Literals include strings, numbers, and booleans

### Conditionals

Conditionals use `when` and `otherwise` to define execution paths:

```vectis
when condition {
    // true branch
}
otherwise {
    // false branch
}
```

### Operator Precedence

Operator precedence follows standard mathematical rules:
1. Parentheses `()`
2. Exponentiation `**`
3. Multiplication `*`, Division `/`
4. Addition `+`, Subtraction `-`
5. Comparison operators `>=`, `<=`, `==`, `!=`
6. Logical operators `&&`, `||`

## Valid Examples

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

## Invalid Examples

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