# Compiler Pipeline

## 1. Source

VECTIS source is UTF-8 text. File and source positions are preserved through tokens and AST spans for deterministic diagnostics.

## 2. Lexer

`vectis.lexer` converts characters into typed tokens. It recognizes declarations/statements, literals, punctuation, boolean/logical/comparison/arithmetic operators, comments, and identifiers.

## 3. Parser

`vectis.parser` produces the canonical AST. Function-call syntax is represented by `CallExpression`; computed declarations use `LetDeclaration`; mission invariants use `AssertStatement`.

## 4. Semantic analyzer

`vectis.semantic` validates declaration uniqueness, reference existence, built-in function names and arity, selected type constraints, boolean conditions/assertions, and numeric confidence values.

## 5. Execution graph compiler

`vectis.compiler` lowers valid AST statements into an `ExecutionGraph` with typed nodes and explicit edges. Reference dependencies become dependency edges. `when` blocks receive explicit true/false edges. Assertions become guard dependencies for later statements in the same block.

The compiler performs only deterministic constant folding using the pure evaluator and values already known at compile time.

## 6. Runtime

The runtime schedules the graph in deterministic topological order and evaluates canonical expressions against actual node values. Compiler and runtime share the same pure expression evaluator to avoid divergent expression semantics.

## 7. Capability adapters

External effects remain outside the compiler. Runtime handlers and explicit adapters provide bounded filesystem, process, or HTTP integration when the embedding application chooses to configure them.
