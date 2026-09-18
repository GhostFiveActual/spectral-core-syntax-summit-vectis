```markdown
# VECTIS Quickstart Guide

Welcome to the VECTIS Quickstart Guide! This guide will help you get started with VECTIS, a powerful and flexible programming language designed for building complex systems.

## Installation

To install VECTIS, you can use pip:

```sh
pip install vectis
```

## Tutorial

### Writing Your First VECTIS Program

Let's start by writing a simple VECTIS program. Create a file named `hello.vectis` with the following content:

```vectis
mission hello {
    print("Hello, VECTIS!");
}
```

### Running Your VECTIS Program

To run your VECTIS program, use the `run` command:

```sh
vectis run hello.vectis
```

This will compile and execute your program, and you should see the output:

```
Hello, VECTIS!
```

## Syntax Reference

### Basic Syntax

VECTIS uses a simple and expressive syntax. Here are some basic constructs:

- **Statements**: Statements are the building blocks of a VECTIS program.
- **Expressions**: Expressions evaluate to a value.
- **Blocks**: Blocks group multiple statements together.

### Example

```vectis
mission hello {
    let x = 10;
    let y = 20;
    let sum = x + y;
    print(sum);
}
```

## Compiler Explanation

The VECTIS compiler converts your source code into an execution graph. This graph represents the sequence of operations that will be executed.

### Compilation Steps

1. **Lexical Analysis**: The source code is broken down into tokens.
2. **Syntax Analysis**: The tokens are parsed into an abstract syntax tree (AST).
3. **Semantic Analysis**: The AST is checked for errors and type correctness.
4. **Code Generation**: The AST is converted into an execution graph.

## Runtime Explanation

The VECTIS runtime executes the execution graph deterministically. This means that the same input will always produce the same output.

### Runtime Steps

1. **Graph Execution**: The nodes in the execution graph are executed in a topological order.
2. **State Management**: The state of each node is tracked during execution.
3. **Error Handling**: Errors are propagated through the graph dependencies.

## Examples

### Example 1: Simple Mission

```vectis
mission hello {
    print("Hello, VECTIS!");
}
```

### Example 2: Conditional Statement

```vectis
mission conditional {
    let x = 10;
    if x > 5 {
        print("x is greater than 5");
    } else {
        print("x is not greater than 5");
    }
}
```

## Troubleshooting

### Common Issues

- **Syntax Errors**: Check your source code for any syntax errors.
- **Runtime Errors**: Ensure that your program is free of runtime errors.

### Debugging

Use the `check` command to validate your source code:

```sh
vectis check hello.vectis
```

This will help you identify any issues in your program.

---

That's it! You now have a basic understanding of VECTIS. Happy coding!
```
