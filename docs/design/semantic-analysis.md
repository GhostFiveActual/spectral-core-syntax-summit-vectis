```markdown
# Semantic Analysis

## Overview

The semantic analyzer is a crucial component of the VECTIS compiler, responsible for validating the structure and semantics of the source code. It ensures that all declarations are correctly referenced, types are valid, and capabilities are properly utilized. The analyzer produces deterministic diagnostics to help developers identify and fix issues in their code.

## Key Features

1. **Reference Validation**: Ensures that all references in the code resolve to valid declarations.
2. **Type Validation**: Validates that values have the correct types, following the VECTIS type model.
3. **Capability Validation**: Ensures that all required capabilities are explicitly enabled and validated through capability adapters.
4. **Diagnostic Production**: Generates detailed diagnostics with source location information to help developers understand and fix issues.

## Detailed Workflow

1. **Parsing**: The source code is first parsed into an abstract syntax tree (AST) using the VECTIS lexer.
2. **Semantic Analysis**: The AST is then traversed by the semantic analyzer to perform the following checks:
   - **Reference Resolution**: Validates that all references (e.g., variable names, function calls) resolve to valid declarations.
   - **Type Checking**: Ensures that all values have the correct types, following the VECTIS type model.
   - **Capability Validation**: Checks that all required capabilities are explicitly enabled and validated through capability adapters.
3. **Diagnostic Generation**: If any issues are found during the analysis, the semantic analyzer generates detailed diagnostics with source location information.

## Example Usage

Here is an example of how the semantic analyzer can be used in the VECTIS compiler:

```python
from vectis.ast import Program, PublishStatement, StringLiteral
from vectis.diagnostic import DiagnosticCode, error_diagnostic
from vectis.source_span import SourceSpan
from vectis.semantic import SemanticAnalyzer

# Create a simple program with a publish statement
publish = PublishStatement(
    value=StringLiteral(
        value="output",
        span=SourceSpan(
            start=SourcePosition(line=1, column=1, file="test"),
            end=SourcePosition(line=1, column=12, file="test"),
        ),
    ),
    span=SourceSpan(
        start=SourcePosition(line=1, column=1, file="test"),
        end=SourcePosition(line=1, column=12, file="test"),
    ),
)
program = Program(statements=(publish,), span=SourceSpan(
    start=SourcePosition(line=1, column=1, file="test"),
    end=SourcePosition(line=1, column=12, file="test"),
))

# Create a semantic analyzer and analyze the program
analyzer = SemanticAnalyzer(program)
diagnostics = analyzer.analyze()

# Check for diagnostics
if diagnostics:
    for diagnostic in diagnostics:
        print(diagnostic.render())
else:
    print("No diagnostics found.")
```

In this example, the semantic analyzer is used to analyze a simple program with a publish statement. If any issues are found, the diagnostics are printed to the console.

## Conclusion

The semantic analyzer is a vital part of the VECTIS compiler, ensuring that the source code is valid and free of errors. By following the VECTIS type model and validating references, types, and capabilities, the semantic analyzer helps developers write correct and efficient code.
```

## Semantic Scope and Resolution

Semantic analysis uses deterministic lexical scope. The program establishes
the outer scope, while nested mission and conditional blocks establish child
scope boundaries. A reference resolves from the innermost active scope outward
to enclosing declarations. A declaration that exists only inside a child scope
does not implicitly become visible outside that block.

Type validation, reference resolution, and capability validation are semantic
operations performed before IR generation. Any invalid semantic relationship
produces a deterministic diagnostic tied to the source span represented by the
AST. The semantic analyzer does not execute capabilities and does not grant
runtime authority; capability enforcement remains the responsibility of the
runtime and explicit adapters.

This separation keeps semantic meaning deterministic: source structure,
scope, references, types, capabilities, and diagnostics are resolved through
defined compiler rules rather than probabilistic inference.
