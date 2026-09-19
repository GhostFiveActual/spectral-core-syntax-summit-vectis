# VECTIS Studio

VECTIS Studio is the local-first graphical application bundled with the `vectis-lang` package.

## Launch

```bash
vectis studio
```

or:

```bash
vectis app
```

Options:

```text
--host HOST
--port PORT
--no-browser
--allow-remote
```

The default binding is `127.0.0.1:8765`. A non-loopback host is rejected unless `--allow-remote` is supplied explicitly.

## Workspace

Studio provides:

- mission source editor,
- line numbers and cursor position,
- example selector,
- formatter,
- Check / Plan / Run actions,
- execution metrics,
- native SVG execution-graph visualization,
- runtime state/value table,
- diagnostics panel,
- raw plan JSON,
- AST JSON,
- built-in function reference.

Keyboard shortcuts:

- `Ctrl+Enter` — run mission
- `Ctrl+Shift+F` — format mission
- `Tab` — insert four spaces in the editor

## Local API

Studio is served by the Python package and uses local JSON endpoints:

```text
GET  /api/health
GET  /api/examples
GET  /api/builtins
POST /api/check
POST /api/parse
POST /api/plan
POST /api/run
POST /api/format
```

Request bodies use `Content-Type: application/json` and provide a `source` string.

The Studio runtime does not automatically grant filesystem, process, or HTTP capabilities.

## Front-end boundary

Studio ships plain HTML, CSS, and JavaScript inside the wheel. It has no external CDN dependency and does not use JavaScript `eval`, `new Function`, or HTML injection for compiler output.

## Future desktop packaging

The packaged local application is deliberately web-runtime neutral. A later release can wrap the same local server/UI in a desktop shell without changing VECTIS language semantics. Tauri or another lightweight shell can be evaluated separately once the browser-based Studio contract stabilizes.
