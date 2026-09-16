```markdown
# Capability Model

## Overview

The capability model in VECTIS is designed to ensure that all operations are explicitly declared and that any implicit privileged behavior is denied. This model is crucial for maintaining security and predictability in the system.

## Capability Declarations

A capability declaration is a statement that explicitly grants a capability to a node in the execution graph. This is done using the `RequireStatement` and `RequestStatement` in the VECTIS AST.

### Example

```python
require_capability = RequireStatement(
    capability=StringLiteral(value="read_file"),
    span=point_span(file="example.py", line=10, column=5)
)

request_capability = RequestStatement(
    capability=StringLiteral(value="write_file"),
    span=point_span(file="example.py", line=15, column=5)
)
```

## Unavailable Capabilities Denied

If a node attempts to use a capability that has not been explicitly granted, the system will deny the operation and raise a `CapabilityError`.

### Example

```python
class CapabilityError(DiagnosticError):
    def __init__(self, capability: Expression, span: SourceSpan) -> None:
        super().__init__(
            diagnostic=error_diagnostic(
                code=DiagnosticCode.CAPABILITY_DENIED,
                message=f"Capability '{capability.value}' denied",
                span=span,
            )
        )
```

## No Implicit Privileged Behavior

The capability model ensures that no operations are performed implicitly. All capabilities must be explicitly requested or required.

### Example

```python
def execute_program(program: Program) -> ExecutionGraph:
    graph = ExecutionGraph(nodes=(), edges=())

    for statement in program.statements:
        if isinstance(statement, RequireStatement):
            if statement.capability.value not in graph.node_ids:
                raise CapabilityError(
                    capability=statement.capability,
                    span=statement.span,
                )

        if isinstance(statement, RequestStatement):
            if statement.capability.value not in graph.node_ids:
                raise CapabilityError(
                    capability=statement.capability,
                    span=statement.span,
                )

        # Add other statement types to the graph

    return graph
```

## Capability Tests

To ensure that the capability model is working correctly, we need to write tests that check for the presence of capability declarations and the denial of unavailable capabilities.

### Example

```python
def test_capability_declaration():
    program = Program(
        statements=(
            RequireStatement(
                capability=StringLiteral(value="read_file"),
                span=point_span(file="test_capability.py", line=10, column=5)
            ),
            RequestStatement(
                capability=StringLiteral(value="write_file"),
                span=point_span(file="test_capability.py", line=15, column=5)
            ),
        )
    )

    graph = execute_program(program)

    assert "read_file" in graph.node_ids
    assert "write_file" in graph.node_ids

def test_unavailable_capability_denied():
    program = Program(
        statements=(
            RequestStatement(
                capability=StringLiteral(value="delete_file"),
                span=point_span(file="test_capability.py", line=20, column=5)
            ),
        )
    )

    with pytest.raises(CapabilityError):
        execute_program(program)
```

## Conclusion

The capability model in VECTIS ensures that all operations are explicitly declared and that any implicit privileged behavior is denied. This model is crucial for maintaining security and predictability in the system. By following the guidelines in this document, you can ensure that your VECTIS programs are secure and reliable.
```
