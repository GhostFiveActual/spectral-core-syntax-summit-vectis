# VECTIS Normative Grammar

Status: normative.

## 1. Purpose

This document defines the concrete grammar of the current VECTIS language.

The lexical specification defines how source text becomes tokens. This
grammar defines how those tokens form syntax. The AST invariants define the
typed structures produced by a conforming parser. The semantic model defines
meaning after parsing.

When this document conflicts with `syntax-draft.md`, this document is
authoritative.

## 2. Notation

The grammar uses EBNF-like notation.

- `"text"` denotes an exact token value.
- `IDENTIFIER`, `STRING`, and `NUMBER` denote lexer token classes.
- `[ X ]` means zero or one occurrence of X.
- `{ X }` means zero or more occurrences of X.
- `( A | B )` means one alternative.
- `EOF` means the end of the token stream.

Whitespace and comments are handled by the lexer and do not appear in the
semantic parser token stream.

## 3. Program

```ebnf
program =
    { statement },
    EOF ;
```

A program may be empty.

A `Program` AST node contains statements in source order.

## 4. Statements

```ebnf
statement =
      mission_statement
    | source_statement
    | analyze_statement
    | require_statement
    | request_statement
    | publish_statement
    | citations_statement
    | confidence_statement
    | when_statement
    ;
```

A standalone expression is not a statement in the current language.

`otherwise` is not an independent statement. It may occur only immediately
after the body of a `when_statement`.

## 5. Blocks

```ebnf
block =
    "{",
    { statement },
    "}" ;
```

A block may be empty.

A `Block` AST node contains its statements in source order.

## 6. Mission Declaration

```ebnf
mission_statement =
    "mission",
    STRING,
    block ;
```

The string value becomes `Mission.name`.

Example:

```vectis
mission "Accessibility research" {
    publish report;
}
```

## 7. Source Declaration

```ebnf
source_statement =
    "source",
    IDENTIFIER,
    expression,
    ";" ;
```

The identifier becomes `SourceDeclaration.name`.

The expression becomes `SourceDeclaration.value`.

Example:

```vectis
source web "accessible developer tools";
```

The current grammar deliberately uses an expression value rather than the
nested source block shown in the historical syntax draft. The canonical AST
contains a source name and value, not a source body.

## 8. Analyze Declaration

```ebnf
analyze_statement =
    "analyze",
    IDENTIFIER,
    [ expression ],
    ";" ;
```

The identifier becomes `AnalyzeDeclaration.name`.

If present, the expression becomes `AnalyzeDeclaration.value`. Otherwise the
AST value is `None`.

Examples:

```vectis
analyze findings;
analyze score confidence;
```

## 9. Capability and Output Statements

```ebnf
require_statement =
    "require",
    expression,
    ";" ;

request_statement =
    "request",
    expression,
    ";" ;

publish_statement =
    "publish",
    expression,
    ";" ;

confidence_statement =
    "confidence",
    expression,
    ";" ;
```

These map respectively to:

- `RequireStatement.capability`
- `RequestStatement.capability`
- `PublishStatement.value`
- `ConfidenceStatement.value`

Examples:

```vectis
require citations;
request review;
publish report;
confidence 0.95;
```

## 10. Citations

```ebnf
citations_statement =
    "citations",
    "[",
    [ expression, { ",", expression } ],
    "]",
    ";" ;
```

The expressions become `CitationsStatement.values` in source order.

Examples:

```vectis
citations [];
citations [primary_source];
citations [primary_source, secondary_source];
```

The square-bracket syntax is currently specific to citation collections. The
current AST does not define a general list-expression node.

## 11. Conditional

```ebnf
when_statement =
    "when",
    expression,
    block,
    [ "otherwise", block ] ;
```

The expression becomes `WhenStatement.condition`.

The first block becomes `WhenStatement.body`.

The optional second block becomes `WhenStatement.otherwise`.

Example:

```vectis
when confidence >= 0.80 {
    publish report;
} otherwise {
    request review;
}
```

`otherwise` binds to the immediately preceding `when` whose body has just
closed.

## 12. Expressions

Expression parsing uses the following precedence levels, from lowest to
highest:

1. logical OR: `||`
2. logical AND: `&&`
3. equality: `==`, `!=`
4. comparison: `>=`, `<=`
5. additive: `+`, `-`
6. multiplicative: `*`, `/`
7. unary: `!`, `+`, `-`
8. primary expressions

All binary operators are left-associative.

Unary operators are right-associative.

```ebnf
expression =
    logical_or ;

logical_or =
    logical_and,
    { "||", logical_and } ;

logical_and =
    equality,
    { "&&", equality } ;

equality =
    comparison,
    { ( "==" | "!=" ), comparison } ;

comparison =
    additive,
    { ( ">=" | "<=" ), additive } ;

additive =
    multiplicative,
    { ( "+" | "-" ), multiplicative } ;

multiplicative =
    unary,
    { ( "*" | "/" ), unary } ;

unary =
      ( "!" | "+" | "-" ), unary
    | primary
    ;

primary =
      STRING
    | NUMBER
    | boolean_literal
    | reference
    | "(", expression, ")"
    ;
```

The current language does not define exponentiation.

The current language does not define function-call expressions.

The current language does not define general list expressions.

## 13. Boolean Literals

The current lexer does not reserve `true` and `false` as keywords. For this
language version they are contextual literals.

```ebnf
boolean_literal =
      IDENTIFIER("true")
    | IDENTIFIER("false")
    ;
```

When an identifier token has the exact value `true` or `false` in primary
expression position, the parser produces `BooleanLiteral`.

Matching is case-sensitive.

Therefore:

```vectis
true
false
```

are boolean literals, while:

```vectis
True
FALSE
```

are ordinary references.

`true` and `false` cannot be used as symbolic references in primary
expression position in this language version.

## 14. References

```ebnf
reference =
    IDENTIFIER ;
```

Except for the contextual boolean literals `true` and `false`, an identifier
in expression position produces `Reference`.

Name resolution is not performed by the parser.

## 15. Numeric Signs and Unary Operators

The lexical specification permits a leading `+` or `-` to be incorporated
into a numeric token when immediately followed by a digit.

Therefore:

```vectis
-42
+3.5
```

are each one `NUMBER` token.

The parser must still support unary `+` and `-` when the lexer emits them as
operator tokens, such as:

```vectis
-value
!ready
```

The parser must not attempt to reconstruct lexical spelling that the lexer
has already classified.

## 16. Statement Terminators

Simple declarations and action statements end with `;`.

The following require semicolons:

- `source`
- `analyze`
- `require`
- `request`
- `publish`
- `citations`
- `confidence`

`mission`, `when`, and blocks do not take a trailing semicolon.

Semicolons make statement boundaries deterministic because whitespace and
newlines are not semantic parser tokens.

## 17. Source Spans

Every AST node produced by the parser must use the canonical `SourceSpan`.

Leaf-node spans cover the token or tokens represented by the leaf.

Unary-expression spans begin at the unary operator and end at the operand.

Binary-expression spans begin at the left operand and end at the right
operand.

Block spans begin at `{` and end at `}`.

Statement spans begin at the statement keyword and end at:

- the terminating `;` for simple statements;
- the closing `}` for a mission;
- the final closing `}` of the `otherwise` block when present for a `when`;
- otherwise the closing `}` of the primary `when` block.

Program spans cover the first through final source token.

For an empty token stream, the parser must create a deterministic zero-width
program span at line 1, column 1 of the parser's source file.

The parser must never manufacture unrelated source locations or use a
different source-location model.

## 18. Syntax Diagnostics

A conforming parser must reject at least:

- unknown statement starts;
- standalone `otherwise`;
- missing mission name;
- missing declaration name;
- missing required expression;
- missing `;`;
- missing `{`;
- missing `}`;
- missing `]`;
- malformed citation lists;
- malformed parenthesized expressions;
- unexpected trailing tokens;
- incomplete binary expressions.

Every parser diagnostic must identify a canonical source location and describe
what syntax was expected.

Parser diagnostics are syntax diagnostics. Name resolution, duplicate names,
type compatibility, capability validation, and execution validity belong to
semantic analysis.

## 19. AST Mapping

Concrete syntax maps to the canonical AST as follows:

| Production | AST |
| --- | --- |
| `program` | `Program` |
| `block` | `Block` |
| `mission_statement` | `Mission` |
| `source_statement` | `SourceDeclaration` |
| `analyze_statement` | `AnalyzeDeclaration` |
| `require_statement` | `RequireStatement` |
| `request_statement` | `RequestStatement` |
| `publish_statement` | `PublishStatement` |
| `citations_statement` | `CitationsStatement` |
| `confidence_statement` | `ConfidenceStatement` |
| `when_statement` | `WhenStatement` |
| `STRING` | `StringLiteral` |
| `NUMBER` | `NumberLiteral` |
| contextual `true` / `false` | `BooleanLiteral` |
| other `IDENTIFIER` | `Reference` |
| unary production | `UnaryExpression` |
| binary production | `BinaryExpression` |

The parser must use these canonical classes rather than defining substitute
AST types.

## 20. Conformance

A parser conforms to this grammar only if it demonstrates all of the
following:

1. every statement production;
2. empty and populated blocks;
3. optional `analyze` values;
4. empty, single, and multiple citation collections;
5. `when` with and without `otherwise`;
6. every expression precedence level;
7. left associativity of binary operators;
8. unary expressions;
9. parenthesized expressions;
10. string, number, boolean, and reference primaries;
11. exact AST node classes;
12. canonical source spans;
13. valid official examples;
14. rejection of official invalid examples;
15. useful syntax diagnostics with source locations.
