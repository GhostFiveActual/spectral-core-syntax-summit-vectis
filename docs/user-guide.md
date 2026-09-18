```markdown
# VECTIS User Guide

## Installation

To install VECTIS, follow these steps:

1. Ensure you have Python 3.8 or later installed.
2. Run the following command to install VECTIS using pip:

   ```sh
   pip install vectis
   ```

## Tutorial

This tutorial will guide you through the basics of using VECTIS.

### Step 1: Writing a Simple Program

Create a new file named `example.vectis` and add the following code:

```vectis
program example {
    source my_source {
        data = "Hello, VECTIS!"
    }

    mission my_mission {
        request my_request {
            source = my_source
        }
    }
}
```

### Step 2: Compiling the Program

Run the following command to compile your program:

```sh
vectis compile example.vectis
```

### Step 3: Running the Compiled Program

Run the following command to execute the compiled program:

```sh
vectis run example.vectis
```

## Syntax Reference

### Program

A program is defined using the `program` keyword followed by the program name and a block of statements.

```vectis
program example {
    // Statements go here
}
```

### Source Declaration

A source declaration defines a data source.

```vectis
source my_source {
    data = "Hello, VECTIS!"
}
```

### Mission Declaration

A mission declaration defines a task to be executed.

```vectis
mission my_mission {
    request my_request {
        source = my_source
    }
}
```

### Request Declaration

A request declaration specifies the source to be used.

```vectis
request my_request {
    source = my_source
}
```

## Compiler Explanation

The VECTIS compiler processes a program and generates an execution graph.

### Semantic Analysis

The compiler performs semantic analysis to ensure the program is valid.

### Graph Construction

The compiler constructs an execution graph based on the program's structure.

## Runtime Explanation

The VECTIS runtime executes the execution graph.

### Node Execution

Nodes in the graph are executed in a topological order.

### Error Handling

The runtime handles errors and provides diagnostics.

## Examples

### Example 1: Simple Program

```vectis
program example {
    source my_source {
        data = "Hello, VECTIS!"
    }

    mission my_mission {
        request my_request {
            source = my_source
        }
    }
}
```

### Example 2: Complex Program

```vectis
program complex {
    source source1 {
        data = "Data from source 1"
    }

    source source2 {
        data = "Data from source 2"
    }

    mission mission1 {
        request request1 {
            source = source1
        }
    }

    mission mission2 {
        request request2 {
            source = source2
        }
    }
}
```

## Troubleshooting

### Common Issues

- **Compilation Errors**: Check the diagnostics for errors in your program.
- **Runtime Errors**: Check the runtime logs for errors during execution.

### Solutions

- **Fix Errors**: Address the errors reported by the compiler or runtime.
- **Update VECTIS**: Ensure you are using the latest version of VECTIS.
- **Consult Documentation**: Refer to the VECTIS documentation for more information.
```

This user guide provides a comprehensive overview of installing, using, and troubleshooting VECTIS. It includes installation instructions, a tutorial, syntax reference, compiler and runtime explanations, examples, and troubleshooting tips.

## Language and runtime contract

This guide documents the stable VECTIS user-facing contract. VECTIS source is parsed and compiled deterministically, and runtime operations remain constrained by explicit capability authorization. Capabilities define which external effects are available to a workflow; unavailable authority is denied rather than inferred. Diagnostics remain explicit and machine-readable, while execution uses the canonical compiler, execution graph, runtime, and adapters.

Contract concepts: capability.
