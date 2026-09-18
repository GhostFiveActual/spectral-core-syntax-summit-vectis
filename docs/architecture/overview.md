```markdown
# Technical Architecture Overview

## System Architecture

The VECTIS system is designed to be modular and extensible, with a focus on deterministic execution and runtime capabilities. The core components include the IR (Intermediate Representation), the Runtime, and the ExecutionGraph.

## Compiler Stages

1. **Parsing**: Converts source code into an abstract syntax tree (AST).
2. **IR Generation**: Translates the AST into an IR representation.
3. **Optimization**: Applies optimizations to the IR to improve performance.
4. **Code Generation**: Translates the optimized IR into executable code.

## IR Design

The IR is designed to be a high-level, structured representation of the program. It includes nodes and edges that represent the program's structure and dependencies. The IR is designed to be easily extensible and to support a wide range of programming languages.

## Runtime Design

The Runtime is responsible for executing the IR in a deterministic manner. It uses a topological sort to determine the order in which nodes should be executed. The Runtime also handles dependencies between nodes and propagates failures through the graph.

## Security Model

The VECTIS system includes a security model that ensures that only authorized operations are performed. The model includes capabilities that define the set of operations that can be performed by each node. The Runtime checks these capabilities before executing a node.

## Design Tradeoffs

1. **Determinism**: The system is designed to be deterministic, meaning that the same input will always produce the same output. This is achieved by using a topological sort to determine the order in which nodes should be executed.
2. **Extensibility**: The system is designed to be extensible, meaning that new nodes and edges can be added to the IR without affecting the existing code.
3. **Performance**: The system is designed to be performant, meaning that it can execute large programs efficiently.
4. **Security**: The system is designed to be secure, meaning that only authorized operations are performed.
```

## Architecture contract completion

### Lexer

The lexer is the first deterministic language stage. It converts VECTIS source text into canonical tokens while preserving source positions for later parser and diagnostic use.

### Parser

The parser consumes lexer tokens and produces the canonical VECTIS abstract syntax tree without executing source.

### Semantic

Semantic analysis validates declarations, references, types, and language constraints before an execution graph is produced.

### Execution Graph

The execution graph is the typed deterministic intermediate representation scheduled by the runtime.

### Capability

Capabilities explicitly authorize external effects. Unavailable capabilities are denied rather than inferred.
