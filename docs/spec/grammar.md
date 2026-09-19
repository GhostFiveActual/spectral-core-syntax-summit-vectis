# VECTIS Normative Grammar — 0.1

Status: normative for the `0.1.x` language line.

## Program

```ebnf
program = { statement }, EOF ;
```

## Statements

```ebnf
statement =
      mission_statement
    | source_statement
    | let_statement
    | analyze_statement
    | require_statement
    | request_statement
    | assert_statement
    | publish_statement
    | citations_statement
    | confidence_statement
    | when_statement
    ;
```

`otherwise` is not an independent statement. It may occur only immediately after a `when` block.

## Blocks

```ebnf
block = "{", { statement }, "}" ;
```

## Mission

```ebnf
mission_statement = "mission", STRING, block ;
```

## Value declarations

```ebnf
source_statement = "source", IDENTIFIER, expression, ";" ;
let_statement    = "let", IDENTIFIER, expression, ";" ;
analyze_statement = "analyze", IDENTIFIER, [ expression ], ";" ;
```

`source` represents initial/input values. `let` represents deterministic computed values. `analyze` remains an explicit analysis node that may be connected to a runtime handler.

## Capability statements

```ebnf
require_statement = "require", expression, ";" ;
request_statement = "request", expression, ";" ;
```

## Assertion

```ebnf
assert_statement = "assert", expression, ";" ;
```

The semantic model requires an assertion expression to be boolean or not statically inferable. At runtime a false assertion fails and gates subsequent statements in the same block.

## Output / metadata statements

```ebnf
publish_statement = "publish", expression, ";" ;
confidence_statement = "confidence", expression, ";" ;

citations_statement =
    "citations", "[",
    [ expression, { ",", expression } ],
    "]", ";" ;
```

## Conditional

```ebnf
when_statement =
    "when", expression, block,
    [ "otherwise", block ] ;
```

## Expressions

Precedence from lowest to highest:

1. `||`
2. `&&`
3. `==`, `!=`
4. `>`, `>=`, `<`, `<=`
5. `+`, `-`
6. `*`, `/`, `%`
7. unary `!`, `+`, `-`
8. primary expressions

```ebnf
expression = logical_or ;

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
    { ( ">" | ">=" | "<" | "<=" ), additive } ;

additive =
    multiplicative,
    { ( "+" | "-" ), multiplicative } ;

multiplicative =
    unary,
    { ( "*" | "/" | "%" ), unary } ;

unary =
      ( "!" | "+" | "-" ), unary
    | primary
    ;

primary =
      STRING
    | NUMBER
    | boolean_literal
    | function_call
    | reference
    | "(", expression, ")"
    ;

function_call =
    IDENTIFIER, "(",
    [ expression, { ",", expression } ],
    ")" ;

reference = IDENTIFIER ;
boolean_literal = "true" | "false" ;
```

## Built-in function names

The parser accepts any identifier-shaped call. Semantic analysis only accepts names in the deterministic built-in registry. The current registry is discoverable with:

```bash
vectis builtins
```

Unknown functions are semantic errors rather than parser errors.

## Deliberate exclusions in 0.1

The grammar does not yet define user-authored `function` declarations, imports/modules, loops, or general list/map expression literals.
