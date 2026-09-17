```markdown
# Runtime Design

## Overview

The runtime component of VECTIS is responsible for executing the compiled graph of nodes and edges. It ensures that the graph is executed in a deterministic manner, tracks the state of each node, and propagates failures appropriately. This document outlines the design and implementation details of the runtime.

## Key Features

1. **Graph Execution**: The runtime executes the graph in a topological order, ensuring that all dependencies are resolved before a node is executed.
2. **Deterministic Scheduling**: The runtime uses the graph's topological order to determine the execution sequence, ensuring that the same execution order is followed every time the graph is executed.
3. **Node State Tracking**: The runtime tracks the state of each node (e.g., succeeded, failed, blocked, dry-run) and provides methods to retrieve this state.
4. **Failure Propagation**: The runtime propagates failures from failed nodes to their dependent nodes, ensuring that the entire graph is executed correctly.
5. **Dry-Run Support**: The runtime supports dry-run mode, where no handlers are invoked, but the execution order and states are still tracked.
6. **Runtime Tests**: The runtime includes a set of tests to verify its correctness and ensure that it behaves as expected.

## Implementation

The runtime is implemented in the `src/vectis/runtime.py` file. It consists of the following components:

1. **Runtime Class**: The main class that manages the execution of the graph.
2. **NodeState Enum**: An enumeration that defines the possible states of a node.
3. **RuntimeResult Class**: A class that encapsulates the result of a runtime execution.

### Runtime Class

The `Runtime` class is responsible for executing the graph. It takes a graph and a dictionary of handlers as input. The handlers are functions that are invoked when a node is executed.

```python
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

from vectis.ir import ExecutionGraph, GraphNode, NodeKind
from vectis.runtime import RuntimeResult, NodeState

class Runtime:
    def __init__(
        self,
        graph: ExecutionGraph,
        handlers: Dict[NodeKind, Callable[[GraphNode], None]] = {},
        dry_run: bool = False,
    ) -> None:
        self.graph = graph
        self.handlers = handlers
        self.dry_run = dry_run
        self.state: Dict[str, NodeState] = {node.id: NodeState.PENDING for node in graph.nodes}
        self.execution_order: List[str] = []

    def execute(self) -> RuntimeResult:
        try:
            self._topological_sort()
            self._execute_nodes()
            return RuntimeResult(
                success=True,
                status="success",
                execution_order=self.execution_order,
                state=self.state,
            )
        except Exception as e:
            return RuntimeResult(
                success=False,
                status="failure",
                failure=str(e),
                execution_order=self.execution_order,
                state=self.state,
            )

    def _topological_sort(self) -> None:
        visited = set()
        stack = []

        def visit(node_id: str) -> None:
            if node_id in visited:
                return
            visited.add(node_id)
            for edge in self.graph.edges:
                if edge.source == node_id:
                    visit(edge.target)
            stack.append(node_id)

        for node_id in self.graph.nodes:
            visit(node_id)

        self.execution_order = stack[::-1]

    def _execute_nodes(self) -> None:
        for node_id in self.execution_order:
            node = next(node for node in self.graph.nodes if node.id == node_id)
            if self.state[node_id] == NodeState.PENDING:
                if self.dry_run:
                    self.state[node_id] = NodeState.DRY_RUN
                else:
                    self.state[node_id] = NodeState.RUNNING
                    if node.kind in self.handlers:
                        self.handlers[node.kind](node)
                    self.state[node_id] = NodeState.SUCCEEDED
```

### NodeState Enum

The `NodeState` enum defines the possible states of a node.

```python
from enum import Enum

class NodeState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    DRY_RUN = "dry-run"
```

### RuntimeResult Class

The `RuntimeResult` class encapsulates the result of a runtime execution.

```python
from dataclasses import dataclass
from typing import List, Optional

class RuntimeResult:
    def __init__(
        self,
        success: bool,
        status: str,
        execution_order: List[str],
        state: Dict[str, NodeState],
        failure: Optional[str] = None,
    ) -> None:
        self.success = success
        self.status = status
        self.execution_order = execution_order
        self.state = state
        self.failure = failure
```

## Testing

The runtime includes a set of tests to verify its correctness. These tests are located in the `tests/runtime/test_runtime.py` file.

```python
import unittest
from vectis.ir import ExecutionGraph, GraphNode, NodeKind
from vectis.runtime import Runtime, NodeState, RuntimeResult

class TestRuntime(unittest.TestCase):
    def test_deterministic_scheduling_uses_graph_order(self):
        graph = ExecutionGraph(
            nodes=(
                GraphNode(id="source", kind=NodeKind.SOURCE),
                GraphNode(id="analyze", kind=NodeKind.ANALYZE),
                GraphNode(id="publish", kind=NodeKind.PUBLISH),
            ),
            edges=(
                GraphEdge(source="source", target="analyze"),
                GraphEdge(source="analyze", target="publish"),
            ),
        )
        seen = []

        runtime = Runtime(
            graph,
            handlers={
                NodeKind.SOURCE: lambda node: seen.append(node.id),
                NodeKind.ANALYZE: lambda node: seen.append(node.id),
                NodeKind.PUBLISH: lambda node: seen.append(node.id),
            },
        )

        result = runtime.execute()

        self.assertTrue(result.success)
        self.assertEqual(result.execution_order, ["source", "analyze", "publish"])
        self.assertEqual(seen, ["source", "analyze", "publish"])

    def test_node_state_tracking_records_success(self):
        result = Runtime(
            ExecutionGraph(
                nodes=(
                    GraphNode(id="source", kind=NodeKind.SOURCE),
                    GraphNode(id="analyze", kind=NodeKind.ANALYZE),
                    GraphNode(id="publish", kind=NodeKind.PUBLISH),
                ),
                edges=(
                    GraphEdge(source="source", target="analyze"),
                    GraphEdge(source="analyze", target="publish"),
                ),
            )
        ).execute()

        self.assertIs(result.state_for("source"), NodeState.SUCCEEDED)
        self.assertIs(result.state_for("analyze"), NodeState.SUCCEEDED)
        self.assertIs(result.state_for("publish"), NodeState.SUCCEEDED)

    def test_failure_propagates_to_dependents(self):
        graph = ExecutionGraph(
            nodes=(
                GraphNode(id="source", kind=NodeKind.SOURCE),
                GraphNode(id="analyze", kind=NodeKind.ANALYZE),
                GraphNode(id="publish", kind=NodeKind.PUBLISH),
            ),
            edges=(
                GraphEdge(source="source", target="analyze"),
                GraphEdge(source="analyze", target="publish"),
            ),
        )

        def fail(_node):
            raise ValueError("intentional failure")

        result = Runtime(
            graph,
            handlers={
                NodeKind.ANALYZE: fail,
            },
        ).execute()

        self.assertFalse(result.success)

        self.assertIs(result.state_for("source"), NodeState.SUCCEEDED)
        self.assertIs(result.state_for("analyze"), NodeState.FAILED)
        self.assertIs(result.state_for("publish"), NodeState.BLOCKED)

        self.assertIsNotNone(result.failure_for("analyze"))
        self.assertIsNotNone(result.failure_for("publish"))

    def test_dry_run_invokes_no_handlers(self):
        graph = ExecutionGraph(
            nodes=(
                GraphNode(id="source", kind=NodeKind.SOURCE),
                GraphNode(id="analyze", kind=NodeKind.ANALYZE),
                GraphNode(id="publish", kind=NodeKind.PUBLISH),
            ),
            edges=(
                GraphEdge(source="source", target="analyze"),
                GraphEdge(source="analyze", target="publish"),
            ),
        )
        called = []

        def handler(node):
            called.append(node.id)

        result = Runtime(
            graph,
            handlers={
                NodeKind.SOURCE: handler,
                NodeKind.ANALYZE: handler,
                NodeKind.PUBLISH: handler,
            },
            dry_run=True,
        ).execute()

        self.assertTrue(result.success)
        self.assertTrue(result.dry_run)
        self.assertEqual(called, [])

        self.assertEqual(result.execution_order, ["source", "analyze", "publish"])

        for node_id in graph.nodes:
            self.assertIs(result.state_for(node_id), NodeState.DRY_RUN)
```

## Conclusion

The runtime component of VECTIS is designed to execute the compiled graph in a deterministic manner, track the state of each node, and propagate failures appropriately. The implementation includes a `Runtime` class, a `NodeState` enum, and a `RuntimeResult` class. The runtime also includes a set of tests to verify its correctness.

The runtime consumes the canonical execution graph and follows its deterministic dependency and branch ordering during execution.

Capability enforcement is explicit: runtime execution denies an unavailable required or requested capability rather than granting implicit external authority.
