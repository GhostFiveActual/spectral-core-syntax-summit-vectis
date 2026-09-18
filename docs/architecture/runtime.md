```markdown
# Runtime Design

The runtime design of VECTIS is responsible for executing the compiled IR and managing the execution environment. The runtime is designed to be modular and extensible, allowing for easy integration of new capabilities and extensions.

## Overview

The runtime consists of several key components:

1. **Execution Engine**: The core component responsible for interpreting and executing the IR.
2. **Capability Resolver**: Manages the resolution of capabilities required by the IR.
3. **Diagnostic Handler**: Handles and reports errors and warnings during execution.
4. **State Manager**: Manages the state of the execution environment, including variables, citations, and confidence levels.

## Execution Engine

The execution engine is responsible for interpreting and executing the IR. It processes each node in the IR and performs the corresponding action. The engine supports the following operations:

- **Mission Execution**: Executes a mission by evaluating its body.
- **Source Declaration**: Declares a source variable and assigns a value.
- **Analyze Declaration**: Analyzes a value and assigns the result to a variable.
- **Require Statement**: Checks if a capability is available and raises an error if not.
- **Request Statement**: Requests a capability and assigns the result to a variable.
- **Publish Statement**: Publishes a value to a channel.
- **Citations Statement**: Updates the citation state with the provided values.
- **Confidence Statement**: Updates the confidence state with the provided value.
- **When Statement**: Executes a block if a condition is true, and an optional otherwise block if the condition is false.

## Capability Resolver

The capability resolver is responsible for resolving capabilities required by the IR. It checks if a capability is available and raises an error if not. The resolver supports the following operations:

- **Check Capabilities**: Checks if all required capabilities are available and returns a list of errors if any are missing.
- **Resolve Capabilities**: Resolves all required capabilities and returns a dictionary of resolved capabilities.

## Diagnostic Handler

The diagnostic handler is responsible for handling and reporting errors and warnings during execution. It supports the following operations:

- **Report Error**: Reports an error with a message and source span.
- **Report Warning**: Reports a warning with a message and source span.

## State Manager

The state manager is responsible for managing the state of the execution environment. It supports the following operations:

- **Get Variable**: Retrieves the value of a variable.
- **Set Variable**: Sets the value of a variable.
- **Update Citations**: Updates the citation state with the provided values.
- **Update Confidence**: Updates the confidence state with the provided value.

## Security Model

The runtime is designed with a security model in mind to ensure that only authorized capabilities are executed. The security model supports the following operations:

- **Check Capability**: Checks if a capability is authorized and raises an error if not.
- **Deny Capability**: Denies a capability and raises an error if it is used.

## Design Tradeoffs

The runtime design has several tradeoffs to consider:

- **Performance**: The runtime must be performant to handle large and complex IRs.
- **Extensibility**: The runtime must be extensible to support new capabilities and extensions.
- **Security**: The runtime must be secure to prevent unauthorized access to capabilities.
- **Usability**: The runtime must be easy to use and understand for developers.

By following these design principles, the VECTIS runtime is designed to be efficient, secure, and extensible, providing a robust foundation for executing IRs.
```
