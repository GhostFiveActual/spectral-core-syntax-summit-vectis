# Semantic Model

## Declarations and References

VECTIS supports the following declaration forms:

- `mission` - Declares a top-level workflow unit
- `source` - Declares data sources
- `analyze` - Declares analysis steps
- `when`/`otherwise` - Declares conditional branches
- `require` - Declares dependencies
- `request` - Declares external requests
- `publish` - Declares output actions
- `citations` - Declares reference sources
- `confidence` - Declares probabilistic metrics

References must resolve to valid declarations through name resolution and scope analysis.

## Value Categories

VECTIS values fall into these categories:

- **Literal** - Direct value representation (strings, numbers, booleans)
- **Expression** - Computed value from operations
- **Reference** - Symbolic reference to a declaration
- **Capability** - Explicitly enabled external functionality
- **Graph Node** - Executable unit in the execution graph
- **Diagnostic** - Error or warning information

## Basic Type Model

VECTIS has the following primitive types:

- `string` - UTF-8 encoded text
- `number` - Floating-point or integer values
- `boolean` - Logical true/false
- `unit` - Nullary value with no type
- `any` - Polymorphic type for untyped values

Type inference follows structural subtyping with explicit type annotations as fallback.

## Capability Semantics

Capabilities are explicit, opt-in features that:

1. Must be declared in the capability adapters
2. Are scoped to specific execution contexts
3. Provide controlled access to external systems
4. Are validated through capability adapters
5. Are explicitly enabled through `require` or `request`

## Execution Dependencies

Execution follows these dependency rules:

- All dependencies must be explicitly declared
- Execution order is determined by the semantic analyzer
- Capabilities are resolved at runtime
- Diagnostic information is attached to execution nodes
- Execution graphs are validated for consistency

## Semantic Invariants

VECTIS enforces these invariants:

1. All declarations must be uniquely named
2. References must resolve to valid declarations
3. Capabilities must be explicitly enabled
4. Execution order must be deterministic
5. All values must have a valid type
6. Diagnostic information must be attached to source spans
7. All capabilities must be validated through adapters
8. Execution graphs must be acyclic and well-formed
9. All semantic analysis must be performed before execution
10. All diagnostics must include source location information