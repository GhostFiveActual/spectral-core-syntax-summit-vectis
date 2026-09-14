# VECTIS Diagnostic System

## Contract

COMP-005 establishes one shared diagnostic model for lexical, syntax, and later
compiler phases. Diagnostics are deterministic compiler data, not free-form
logging strings.

Every diagnostic has a stable diagnostic code, severity, readable message, and
canonical source span. The same diagnostic can be rendered for a human or
serialized into a machine-readable dictionary.

## Severity levels

VECTIS defines two severity levels:

- `error` — compilation cannot continue for the affected input.
- `warning` — compilation may continue, but a condition should be surfaced.

Lexer and parser failures currently use `error`.

## Stable diagnostic codes

The code meanings are stable and must not be silently repurposed.

| Code | Meaning |
| --- | --- |
| `LEX001` | Unterminated string literal |
| `LEX002` | Unsupported bare operator |
| `LEX003` | Unrecognized character |
| `SYN001` | Expected statement / unknown statement start |
| `SYN002` | Standalone `otherwise` |
| `SYN003` | Expected required token or delimiter |
| `SYN004` | Expected expression |
| `SYN005` | Unclosed block |
| `SYN006` | Malformed citation collection |
| `SYN007` | Reserved keyword cannot begin a statement |

Future compiler phases allocate new stable diagnostic codes instead of changing
the meaning of existing codes.

## Source span contract

`Diagnostic.span` is the canonical `SourceSpan` from COMP-001. When a concrete
offending parser token exists, the diagnostic retains that token's full source
span. End-of-input diagnostics use a deterministic point source span after the
final token. Lexer diagnostics use a point source span at the offending lexical
location.

## Human-readable compatibility

`LexerError` and `ParserError` remain catchable `ValueError` subclasses through
`DiagnosticError`. Existing readable exception output remains:

`file:line:column: message`

The structured diagnostic is available through `.diagnostic`. Compatibility
properties `.code`, `.severity`, `.message`, `.span`, `.file`, `.line`, and
`.column` are also exposed.

## Machine-readable form

`Diagnostic.to_dict()` and `DiagnosticError.to_dict()` return JSON-serializable
data:

~~text
{
  "code": "SYN003",
  "severity": "error",
  "message": "expected ';'",
  "source": {
    "file": "example.vectis",
    "start": {"line": 2, "column": 10},
    "end": {"line": 2, "column": 10}
  }
}
~~

This machine-readable form is intended for the CLI, browser playground, editor
integrations, demo tooling, and later execution/reporting systems.

## Phase integration

The lexer maps malformed lexical input to `LEX001` through `LEX003`. The parser
maps syntax failures to `SYN001` through `SYN007`.

Semantic analysis will reuse the shared diagnostic type and allocate a semantic
code range during COMP-006. Semantic diagnostics must remain attached to
canonical source spans.
