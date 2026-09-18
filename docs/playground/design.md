# VECTIS Browser Playground Design

## Purpose

The VECTIS browser playground is a lightweight local interface for
editing VECTIS source, sending it through the deterministic toolchain,
and inspecting its AST, execution graph, and diagnostic output.

It is intentionally a thin interface. The browser does not implement a
second parser, compiler, semantic analyzer, or runtime. VECTIS semantics
remain owned by the canonical Python implementation.

## Browser interface

The playground consists of:

- `index.html` for semantic browser structure;
- `styles.css` for responsive and accessibility-focused presentation;
- `app.js` for interaction with the local API;
- an editable VECTIS source area;
- a valid example program;
- AST output;
- execution-graph output;
- diagnostic output; and
- a live status region.

No third-party browser dependency or CDN is required.

## Example

The browser loads this valid example automatically:

```vectis
mission "Hello VECTIS" {
    source greeting "Hello, VECTIS!";
    publish greeting;
}
```

The example gives a new user an immediately runnable starting point while
still using real VECTIS syntax.

## Local API contract

The browser sends a `POST /api/run` request with
`Content-Type: application/json`.

The request body is:

```json
{
  "source": "VECTIS source text"
}
```

A successful local backend response supplies browser-facing compiler
data:

```json
{
  "ast": {},
  "executionGraph": {},
  "diagnostics": []
}
```

The frontend also accepts `execution_graph` as a compatibility spelling
for the execution graph.

Transport and response failures are presented as diagnostics rather than
evaluated as executable browser content.

## Deterministic boundary

The browser is presentation only. Source must still be parsed,
semantically analyzed, compiled, and executed by the canonical VECTIS
implementation.

The frontend does not use `eval`, dynamic `Function` construction, or
`innerHTML` for compiler results. Returned data is rendered as text.

## Diagnostic presentation

Diagnostics have their own output region and are rendered as structured
JSON text. Failed HTTP requests and malformed API responses are also
displayed in the diagnostic region.

This gives users one predictable place to inspect language and transport
failures.

## Accessibility

Accessibility is part of the playground contract.

The interface provides:

- an explicit label for the source editor;
- native buttons;
- visible keyboard focus indicators;
- keyboard-focusable result panels;
- live status and output regions;
- responsive layout for narrow displays;
- no color-only success or failure signal; and
- reduced-motion handling.

The playground therefore remains usable with keyboard navigation,
assistive technology, and narrow browser layouts.

## Testing

`tests/test_playground_contract.py` verifies the local static interface
without requiring a browser driver or network access.

The tests cover required files, HTML linkage, source editing controls,
accessibility hooks, output regions, the local API contract, safe text
rendering, responsive CSS, documentation concepts, and compilation of
the embedded VECTIS example.
