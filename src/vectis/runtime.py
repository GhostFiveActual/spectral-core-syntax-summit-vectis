"""Deterministic execution runtime for canonical VECTIS execution graphs.

RUN-002 deliberately performs no implicit external I/O. Graph nodes are
scheduled deterministically, explicit handlers may perform node-specific
work, capabilities are checked before privileged capability nodes execute,
and failures propagate through graph dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Mapping

from vectis.capabilities import CapabilityRegistry
from vectis.ir import EdgeKind, ExecutionGraph, GraphNode, NodeKind


class NodeState(str, Enum):
    """Stable runtime state for an execution-graph node."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    DRY_RUN = "dry_run"


class RuntimeExecutionError(RuntimeError):
    """Raised internally when deterministic node execution cannot continue."""


@dataclass(frozen=True, slots=True)
class RuntimeFailure:
    """A stable failure record produced during execution."""

    node_id: str
    message: str


@dataclass(frozen=True, slots=True)
class RuntimeResult:
    """Immutable result of one deterministic runtime execution."""

    success: bool
    dry_run: bool
    execution_order: tuple[str, ...]
    node_states: tuple[tuple[str, NodeState], ...]
    failures: tuple[RuntimeFailure, ...] = ()

    @property
    def status(self) -> str:
        """Return the stable high-level result status."""
        return "success" if self.success else "failure"

    @property
    def states(self) -> dict[str, NodeState]:
        """Return node states as a new mapping."""
        return dict(self.node_states)

    def state_for(self, node_id: str) -> NodeState:
        """Return the final state for one node."""
        for current_id, state in self.node_states:
            if current_id == node_id:
                return state
        raise KeyError(node_id)

    def failure_for(self, node_id: str) -> RuntimeFailure | None:
        """Return the first recorded failure for one node, if any."""
        for failure in self.failures:
            if failure.node_id == node_id:
                return failure
        return None


NodeHandler = Callable[[GraphNode], object]


class Runtime:
    """Execute an immutable :class:`ExecutionGraph` deterministically.

    The graph's canonical ``topological_order()`` is the scheduling authority.
    Runtime itself performs no filesystem, process, network, or other
    privileged operation. Such behavior must be supplied explicitly through
    a node handler and, where applicable, through an available capability.
    """

    def __init__(
        self,
        graph: ExecutionGraph,
        *,
        capabilities: CapabilityRegistry | None = None,
        handlers: Mapping[NodeKind, NodeHandler] | None = None,
        dry_run: bool = False,
    ) -> None:
        if not isinstance(graph, ExecutionGraph):
            raise TypeError("Runtime.graph must be an ExecutionGraph")

        if capabilities is not None and not isinstance(
            capabilities,
            CapabilityRegistry,
        ):
            raise TypeError(
                "Runtime.capabilities must be a CapabilityRegistry or None"
            )

        if not isinstance(dry_run, bool):
            raise TypeError("Runtime.dry_run must be a bool")

        normalized_handlers: dict[NodeKind, NodeHandler] = {}

        if handlers is not None:
            for kind, handler in handlers.items():
                if not isinstance(kind, NodeKind):
                    raise TypeError(
                        "Runtime handler keys must be NodeKind values"
                    )

                if not callable(handler):
                    raise TypeError(
                        f"Runtime handler for {kind.value!r} must be callable"
                    )

                normalized_handlers[kind] = handler

        self.graph = graph
        self.capabilities = capabilities
        self.handlers = normalized_handlers
        self.dry_run = dry_run

        self._states: dict[str, NodeState] = {}
        self._failures: list[RuntimeFailure] = []
        self._execution_order: list[str] = []

    def execute(self) -> RuntimeResult:
        """Execute the graph and return an immutable deterministic result."""
        schedule = self.graph.topological_order()

        self._states = {
            node_id: NodeState.PENDING
            for node_id in schedule
        }
        self._failures = []
        self._execution_order = []

        if self.dry_run:
            for node_id in schedule:
                self._states[node_id] = NodeState.DRY_RUN
                self._execution_order.append(node_id)

            return self._result()

        if not self._check_graph_capabilities():
            for node_id in schedule:
                if self._states[node_id] is NodeState.PENDING:
                    self._states[node_id] = NodeState.BLOCKED

            return self._result()

        for node_id in schedule:
            state = self._states[node_id]

            if state is not NodeState.PENDING:
                continue

            dependency_states = tuple(
                self._states[dependency_id]
                for dependency_id in self.graph.dependencies_of(node_id)
            )

            if any(
                dependency_state in (
                    NodeState.FAILED,
                    NodeState.BLOCKED,
                )
                for dependency_state in dependency_states
            ):
                self._states[node_id] = NodeState.BLOCKED
                self._failures.append(
                    RuntimeFailure(
                        node_id=node_id,
                        message="Blocked by failed dependency",
                    )
                )
                continue

            if any(
                dependency_state is NodeState.SKIPPED
                for dependency_state in dependency_states
            ):
                self._states[node_id] = NodeState.SKIPPED
                continue

            node = self.graph.node(node_id)
            self._states[node_id] = NodeState.RUNNING
            self._execution_order.append(node_id)

            try:
                self._check_node_capability(node)
                value = self._execute_node(node)

                self._states[node_id] = NodeState.SUCCEEDED

                if node.kind is NodeKind.CONDITION:
                    self._select_condition_branch(
                        node,
                        value,
                    )

            except Exception as exc:
                self._states[node_id] = NodeState.FAILED
                self._failures.append(
                    RuntimeFailure(
                        node_id=node_id,
                        message=f"{type(exc).__name__}: {exc}",
                    )
                )

        return self._result()

    def _check_graph_capabilities(self) -> bool:
        """Run the existing capability checker before execution."""
        if self.capabilities is None:
            return True

        diagnostics = self.capabilities.check_capabilities(
            self.graph
        )

        if not diagnostics:
            return True

        for diagnostic in diagnostics:
            self._failures.append(
                RuntimeFailure(
                    node_id="<capability>",
                    message=str(diagnostic),
                )
            )

        return False

    def _check_node_capability(
        self,
        node: GraphNode,
    ) -> None:
        """Deny unavailable explicit capability nodes."""
        if node.kind not in (
            NodeKind.REQUIRE,
            NodeKind.REQUEST,
        ):
            return

        capability_name = node.value

        if (
            not isinstance(capability_name, str)
            or not capability_name.strip()
        ):
            raise RuntimeExecutionError(
                f"{node.kind.value} node {node.id!r} "
                "does not identify a capability"
            )

        if (
            self.capabilities is None
            or not self.capabilities.has_capability(
                capability_name
            )
        ):
            raise RuntimeExecutionError(
                f"Capability {capability_name!r} is unavailable"
            )

    def _execute_node(
        self,
        node: GraphNode,
    ) -> object:
        """Execute one node through an explicitly supplied handler.

        Nodes without handlers are deterministic no-ops. This keeps RUN-002
        free of implicit privileged behavior while later adapter tasks can
        attach explicit execution behavior.
        """
        handler = self.handlers.get(node.kind)

        if handler is None:
            return node.value

        return handler(node)

    def _select_condition_branch(
        self,
        node: GraphNode,
        handler_value: object,
    ) -> None:
        """Skip the inactive branch of a canonical condition node."""
        condition_value = (
            handler_value
            if isinstance(handler_value, bool)
            else node.value
        )

        if not isinstance(condition_value, bool):
            raise RuntimeExecutionError(
                f"Condition node {node.id!r} "
                "did not produce a boolean value"
            )

        selected_kind = (
            EdgeKind.TRUE_BRANCH
            if condition_value
            else EdgeKind.FALSE_BRANCH
        )

        for edge in self.graph.edges:
            if edge.source != node.id:
                continue

            if edge.kind not in (
                EdgeKind.TRUE_BRANCH,
                EdgeKind.FALSE_BRANCH,
            ):
                continue

            if edge.kind is selected_kind:
                continue

            target_state = self._states.get(
                edge.target
            )

            if target_state is NodeState.PENDING:
                self._states[edge.target] = NodeState.SKIPPED

    def _result(self) -> RuntimeResult:
        """Build a stable result in canonical graph order."""
        schedule = self.graph.topological_order()

        failure_states = {
            NodeState.FAILED,
            NodeState.BLOCKED,
        }

        success = not self._failures and not any(
            self._states[node_id] in failure_states
            for node_id in schedule
        )

        return RuntimeResult(
            success=success,
            dry_run=self.dry_run,
            execution_order=tuple(
                self._execution_order
            ),
            node_states=tuple(
                (
                    node_id,
                    self._states[node_id],
                )
                for node_id in schedule
            ),
            failures=tuple(
                self._failures
            ),
        )


# Compatibility aliases for the abandoned RUN-002 draft terminology.
# Runtime and RuntimeResult are the canonical public contract.
DeterministicRuntime = Runtime
ExecutionResult = RuntimeResult
