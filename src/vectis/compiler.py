from __future__ import annotations

from dataclasses import dataclass

from vectis.ast import (
    AnalyzeDeclaration,
    BinaryExpression,
    Block,
    BooleanLiteral,
    CitationsStatement,
    ConfidenceStatement,
    Expression,
    Mission,
    NumberLiteral,
    Program,
    PublishStatement,
    Reference,
    RequestStatement,
    RequireStatement,
    SourceDeclaration,
    Statement,
    StringLiteral,
    UnaryExpression,
    WhenStatement,
)
from vectis.diagnostic import Diagnostic
from vectis.ir import (
    EdgeKind,
    ExecutionGraph,
    GraphEdge,
    GraphNode,
    NodeKind,
)
from vectis.semantic import analyze as analyze_semantics


@dataclass(frozen=True, slots=True)
class CompileResult:
    graph: ExecutionGraph | None
    diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def ok(self) -> bool:
        return self.graph is not None and not self.diagnostics


class CompilationError(ValueError):
    def __init__(self, diagnostics: tuple[Diagnostic, ...]) -> None:
        self.diagnostics = diagnostics

        message = "VECTIS compilation failed"

        if diagnostics:
            rendered = "; ".join(
                diagnostic.render()
                if hasattr(diagnostic, "render")
                else str(diagnostic)
                for diagnostic in diagnostics
            )
            message = f"{message}: {rendered}"

        super().__init__(message)


def _semantic_diagnostics(
    program: Program,
) -> tuple[Diagnostic, ...]:
    result = analyze_semantics(program)

    if result is None:
        return ()

    if isinstance(result, (list, tuple)):
        return tuple(result)

    diagnostics = getattr(
        result,
        "diagnostics",
        None,
    )

    if diagnostics is not None:
        return tuple(diagnostics)

    raise TypeError(
        "vectis.semantic.analyze returned an unsupported result type"
    )


def _expression_text(
    expression: Expression,
) -> str:
    if isinstance(expression, StringLiteral):
        return repr(expression.value)

    if isinstance(expression, NumberLiteral):
        return str(expression.value)

    if isinstance(expression, BooleanLiteral):
        return "true" if expression.value else "false"

    if isinstance(expression, Reference):
        return expression.name

    if isinstance(expression, UnaryExpression):
        return (
            f"{expression.operator}"
            f"{_expression_text(expression.operand)}"
        )

    if isinstance(expression, BinaryExpression):
        return (
            "("
            f"{_expression_text(expression.left)} "
            f"{expression.operator} "
            f"{_expression_text(expression.right)}"
            ")"
        )

    raise TypeError(
        "unsupported VECTIS expression: "
        f"{type(expression).__name__}"
    )


def _scalar_value(
    expression: Expression,
) -> str | int | float | bool | None:
    if isinstance(expression, StringLiteral):
        return expression.value

    if isinstance(expression, NumberLiteral):
        return expression.value

    if isinstance(expression, BooleanLiteral):
        return expression.value

    return None


def _reference_names(
    expression: Expression,
) -> tuple[str, ...]:
    names: list[str] = []

    def visit(current: Expression) -> None:
        if isinstance(current, Reference):
            names.append(current.name)
            return

        if isinstance(current, UnaryExpression):
            visit(current.operand)
            return

        if isinstance(current, BinaryExpression):
            visit(current.left)
            visit(current.right)

    visit(expression)

    return tuple(dict.fromkeys(names))


class _GraphBuilder:
    def __init__(self) -> None:
        self.nodes: list[GraphNode] = []
        self.edges: list[GraphEdge] = []
        self.node_ids: set[str] = set()
        self.edge_keys: set[tuple[str, str, EdgeKind]] = set()
        self.counters: dict[str, int] = {}

    def build(
        self,
        program: Program,
    ) -> ExecutionGraph:
        for statement in program.statements:
            self._compile_statement(statement)

        return ExecutionGraph(
            nodes=tuple(self.nodes),
            edges=tuple(self.edges),
        )

    def _fresh_id(
        self,
        prefix: str,
    ) -> str:
        counter = self.counters.get(prefix, 0)

        while True:
            counter += 1
            candidate = f"{prefix}:{counter:04d}"

            if candidate not in self.node_ids:
                self.counters[prefix] = counter
                return candidate

    def _add_node(
        self,
        node: GraphNode,
    ) -> None:
        if node.id in self.node_ids:
            raise ValueError(
                f"duplicate compiler node id: {node.id}"
            )

        self.node_ids.add(node.id)
        self.nodes.append(node)

    def _add_edge(
        self,
        source: str,
        target: str,
        kind: EdgeKind = EdgeKind.DEPENDENCY,
    ) -> None:
        key = (
            source,
            target,
            kind,
        )

        if key in self.edge_keys:
            return

        self.edge_keys.add(key)

        self.edges.append(
            GraphEdge(
                source=source,
                target=target,
                kind=kind,
            )
        )

    def _add_expression_dependencies(
        self,
        expression: Expression,
        target: str,
    ) -> None:
        for name in _reference_names(expression):
            if name in self.node_ids:
                self._add_edge(
                    name,
                    target,
                    EdgeKind.DEPENDENCY,
                )

    def _compile_block(
        self,
        block: Block,
    ) -> tuple[str, ...]:
        created: list[str] = []

        for statement in block.statements:
            created.extend(
                self._compile_statement(statement)
            )

        return tuple(created)

    def _compile_statement(
        self,
        statement: Statement,
    ) -> tuple[str, ...]:
        if isinstance(statement, Mission):
            return self._compile_block(statement.body)

        if isinstance(statement, SourceDeclaration):
            node_id = statement.name

            self._add_node(
                GraphNode(
                    id=node_id,
                    kind=NodeKind.SOURCE,
                    label=statement.name,
                    value=_scalar_value(statement.value),
                    metadata=(
                        (
                            "expression",
                            _expression_text(statement.value),
                        ),
                    ),
                )
            )

            self._add_expression_dependencies(
                statement.value,
                node_id,
            )

            return (node_id,)

        if isinstance(statement, AnalyzeDeclaration):
            node_id = statement.name

            metadata = ()

            if statement.value is not None:
                metadata = (
                    (
                        "expression",
                        _expression_text(statement.value),
                    ),
                )

            self._add_node(
                GraphNode(
                    id=node_id,
                    kind=NodeKind.ANALYZE,
                    label=statement.name,
                    value=(
                        _scalar_value(statement.value)
                        if statement.value is not None
                        else None
                    ),
                    metadata=metadata,
                )
            )

            if statement.value is not None:
                self._add_expression_dependencies(
                    statement.value,
                    node_id,
                )

            return (node_id,)

        if isinstance(statement, RequireStatement):
            node_id = self._fresh_id("require")

            self._add_node(
                GraphNode(
                    id=node_id,
                    kind=NodeKind.REQUIRE,
                    label="require",
                    value=_scalar_value(statement.capability),
                    metadata=(
                        (
                            "expression",
                            _expression_text(statement.capability),
                        ),
                    ),
                )
            )

            self._add_expression_dependencies(
                statement.capability,
                node_id,
            )

            return (node_id,)

        if isinstance(statement, RequestStatement):
            node_id = self._fresh_id("request")

            self._add_node(
                GraphNode(
                    id=node_id,
                    kind=NodeKind.REQUEST,
                    label="request",
                    value=_scalar_value(statement.capability),
                    metadata=(
                        (
                            "expression",
                            _expression_text(statement.capability),
                        ),
                    ),
                )
            )

            self._add_expression_dependencies(
                statement.capability,
                node_id,
            )

            return (node_id,)

        if isinstance(statement, PublishStatement):
            node_id = self._fresh_id("publish")

            self._add_node(
                GraphNode(
                    id=node_id,
                    kind=NodeKind.PUBLISH,
                    label="publish",
                    value=_scalar_value(statement.value),
                    metadata=(
                        (
                            "expression",
                            _expression_text(statement.value),
                        ),
                    ),
                )
            )

            self._add_expression_dependencies(
                statement.value,
                node_id,
            )

            return (node_id,)

        if isinstance(statement, CitationsStatement):
            node_id = self._fresh_id("citations")

            self._add_node(
                GraphNode(
                    id=node_id,
                    kind=NodeKind.CITATIONS,
                    label="citations",
                    metadata=(
                        (
                            "count",
                            len(statement.values),
                        ),
                        (
                            "values",
                            ", ".join(
                                _expression_text(value)
                                for value in statement.values
                            ),
                        ),
                    ),
                )
            )

            for value in statement.values:
                self._add_expression_dependencies(
                    value,
                    node_id,
                )

            return (node_id,)

        if isinstance(statement, ConfidenceStatement):
            node_id = self._fresh_id("confidence")

            if "CONFIDENCE" not in NodeKind.__members__:
                raise ValueError(
                    "canonical IR does not define "
                    "NodeKind.CONFIDENCE"
                )

            kind = NodeKind.__members__["CONFIDENCE"]

            self._add_node(
                GraphNode(
                    id=node_id,
                    kind=kind,
                    label="confidence",
                    value=_scalar_value(statement.value),
                    metadata=(
                        (
                            "expression",
                            _expression_text(statement.value),
                        ),
                    ),
                )
            )

            self._add_expression_dependencies(
                statement.value,
                node_id,
            )

            return (node_id,)

        if isinstance(statement, WhenStatement):
            condition_id = self._fresh_id("condition")

            self._add_node(
                GraphNode(
                    id=condition_id,
                    kind=NodeKind.CONDITION,
                    label="when",
                    value=_scalar_value(statement.condition),
                    metadata=(
                        (
                            "expression",
                            _expression_text(statement.condition),
                        ),
                    ),
                )
            )

            self._add_expression_dependencies(
                statement.condition,
                condition_id,
            )

            true_nodes = self._compile_block(
                statement.body
            )

            false_nodes: tuple[str, ...] = ()

            if statement.otherwise is not None:
                false_nodes = self._compile_block(
                    statement.otherwise
                )

            if true_nodes:
                self._add_edge(
                    condition_id,
                    true_nodes[0],
                    EdgeKind.TRUE_BRANCH,
                )

            if false_nodes:
                self._add_edge(
                    condition_id,
                    false_nodes[0],
                    EdgeKind.FALSE_BRANCH,
                )

            return (
                condition_id,
                *true_nodes,
                *false_nodes,
            )

        raise TypeError(
            "unsupported VECTIS statement: "
            f"{type(statement).__name__}"
        )


def compile_program(
    program: Program,
) -> CompileResult:
    if not isinstance(program, Program):
        raise TypeError(
            "compile_program requires a Program"
        )

    diagnostics = _semantic_diagnostics(program)

    if diagnostics:
        return CompileResult(
            graph=None,
            diagnostics=diagnostics,
        )

    graph = _GraphBuilder().build(program)

    return CompileResult(
        graph=graph,
        diagnostics=(),
    )


def compile_ast_to_execution_graph(
    program: Program,
) -> ExecutionGraph:
    result = compile_program(program)

    if not result.ok or result.graph is None:
        raise CompilationError(
            result.diagnostics
        )

    return result.graph
