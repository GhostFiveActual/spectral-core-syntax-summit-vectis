from __future__ import annotations

from dataclasses import dataclass

from vectis.ast import (
    AnalyzeDeclaration,
    AssertStatement,
    BinaryExpression,
    Block,
    BooleanLiteral,
    CallExpression,
    CitationsStatement,
    ConfidenceStatement,
    Expression,
    LetDeclaration,
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
from vectis.evaluator import EvaluationError, evaluate_expression
from vectis.formatter import format_expression
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


def _semantic_diagnostics(program: Program) -> tuple[Diagnostic, ...]:
    result = analyze_semantics(program)
    if result is None:
        return ()
    if isinstance(result, (list, tuple)):
        return tuple(result)
    diagnostics = getattr(result, "diagnostics", None)
    if diagnostics is not None:
        return tuple(diagnostics)
    raise TypeError(
        "vectis.semantic.analyze returned an unsupported result type"
    )


def _reference_names(expression: Expression) -> tuple[str, ...]:
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
            return
        if isinstance(current, CallExpression):
            for argument in current.arguments:
                visit(argument)

    visit(expression)
    return tuple(dict.fromkeys(names))


class _GraphBuilder:
    def __init__(self) -> None:
        self.nodes: list[GraphNode] = []
        self.edges: list[GraphEdge] = []
        self.node_ids: set[str] = set()
        self.edge_keys: set[tuple[str, str, EdgeKind]] = set()
        self.counters: dict[str, int] = {}
        self.known_values: dict[str, str | int | float | bool | None] = {}

    def build(self, program: Program) -> ExecutionGraph:
        for statement in program.statements:
            self._compile_statement(statement)
        return ExecutionGraph(
            nodes=tuple(self.nodes),
            edges=tuple(self.edges),
        )

    def _fresh_id(self, prefix: str) -> str:
        counter = self.counters.get(prefix, 0)
        while True:
            counter += 1
            candidate = f"{prefix}:{counter:04d}"
            if candidate not in self.node_ids:
                self.counters[prefix] = counter
                return candidate

    def _add_node(self, node: GraphNode) -> None:
        if node.id in self.node_ids:
            raise ValueError(f"duplicate compiler node id: {node.id}")
        self.node_ids.add(node.id)
        self.nodes.append(node)

    def _add_edge(
        self,
        source: str,
        target: str,
        kind: EdgeKind = EdgeKind.DEPENDENCY,
    ) -> None:
        key = (source, target, kind)
        if key in self.edge_keys:
            return
        self.edge_keys.add(key)
        self.edges.append(GraphEdge(source=source, target=target, kind=kind))

    def _add_expression_dependencies(
        self,
        expression: Expression,
        target: str,
    ) -> None:
        for name in _reference_names(expression):
            if name in self.node_ids:
                self._add_edge(name, target, EdgeKind.DEPENDENCY)

    def _try_value(self, expression: Expression) -> str | int | float | bool | None:
        try:
            return evaluate_expression(expression, self.known_values)
        except EvaluationError:
            return None

    def _expression_metadata(self, expression: Expression):
        return (("expression", format_expression(expression)),)

    def _compile_block(self, block: Block) -> tuple[str, ...]:
        created: list[str] = []
        assertion_guards: list[str] = []

        for statement in block.statements:
            statement_nodes = self._compile_statement(statement)

            for guard_id in assertion_guards:
                for node_id in statement_nodes:
                    if node_id != guard_id:
                        self._add_edge(
                            guard_id,
                            node_id,
                            EdgeKind.DEPENDENCY,
                        )

            created.extend(statement_nodes)

            if isinstance(statement, AssertStatement):
                assertion_guards.extend(statement_nodes)

        return tuple(created)

    def _compile_named_value(
        self,
        *,
        node_id: str,
        kind: NodeKind,
        expression: Expression,
    ) -> tuple[str, ...]:
        value = self._try_value(expression)
        self._add_node(
            GraphNode(
                id=node_id,
                kind=kind,
                label=node_id,
                value=value,
                metadata=self._expression_metadata(expression),
            )
        )
        self._add_expression_dependencies(expression, node_id)
        if value is not None:
            self.known_values[node_id] = value
        return (node_id,)

    def _compile_statement(self, statement: Statement) -> tuple[str, ...]:
        if isinstance(statement, Mission):
            return self._compile_block(statement.body)

        if isinstance(statement, SourceDeclaration):
            return self._compile_named_value(
                node_id=statement.name,
                kind=NodeKind.SOURCE,
                expression=statement.value,
            )

        if isinstance(statement, LetDeclaration):
            return self._compile_named_value(
                node_id=statement.name,
                kind=NodeKind.VALUE,
                expression=statement.value,
            )

        if isinstance(statement, AnalyzeDeclaration):
            node_id = statement.name
            metadata = ()
            value = None
            if statement.value is not None:
                value = self._try_value(statement.value)
                metadata = self._expression_metadata(statement.value)
            self._add_node(
                GraphNode(
                    id=node_id,
                    kind=NodeKind.ANALYZE,
                    label=statement.name,
                    value=value,
                    metadata=metadata,
                )
            )
            if statement.value is not None:
                self._add_expression_dependencies(statement.value, node_id)
            if value is not None:
                self.known_values[node_id] = value
            return (node_id,)

        if isinstance(statement, RequireStatement):
            return self._compile_action(
                prefix="require",
                kind=NodeKind.REQUIRE,
                expression=statement.capability,
            )

        if isinstance(statement, RequestStatement):
            return self._compile_action(
                prefix="request",
                kind=NodeKind.REQUEST,
                expression=statement.capability,
            )

        if isinstance(statement, AssertStatement):
            return self._compile_action(
                prefix="assert",
                kind=NodeKind.ASSERT,
                expression=statement.condition,
            )

        if isinstance(statement, PublishStatement):
            return self._compile_action(
                prefix="publish",
                kind=NodeKind.PUBLISH,
                expression=statement.value,
            )

        if isinstance(statement, ConfidenceStatement):
            return self._compile_action(
                prefix="confidence",
                kind=NodeKind.CONFIDENCE,
                expression=statement.value,
            )

        if isinstance(statement, CitationsStatement):
            node_id = self._fresh_id("citations")
            self._add_node(
                GraphNode(
                    id=node_id,
                    kind=NodeKind.CITATIONS,
                    label="citations",
                    metadata=(
                        ("count", len(statement.values)),
                        (
                            "values",
                            ", ".join(
                                format_expression(value)
                                for value in statement.values
                            ),
                        ),
                    ),
                )
            )
            for value in statement.values:
                self._add_expression_dependencies(value, node_id)
            return (node_id,)

        if isinstance(statement, WhenStatement):
            condition_id = self._fresh_id("condition")
            condition_value = self._try_value(statement.condition)
            self._add_node(
                GraphNode(
                    id=condition_id,
                    kind=NodeKind.CONDITION,
                    label="when",
                    value=condition_value,
                    metadata=self._expression_metadata(statement.condition),
                )
            )
            self._add_expression_dependencies(statement.condition, condition_id)

            true_nodes = self._compile_block(statement.body)
            false_nodes: tuple[str, ...] = ()
            if statement.otherwise is not None:
                false_nodes = self._compile_block(statement.otherwise)

            for node_id in true_nodes:
                self._add_edge(
                    condition_id,
                    node_id,
                    EdgeKind.TRUE_BRANCH,
                )
            for node_id in false_nodes:
                self._add_edge(
                    condition_id,
                    node_id,
                    EdgeKind.FALSE_BRANCH,
                )

            return (condition_id, *true_nodes, *false_nodes)

        raise TypeError(
            "unsupported VECTIS statement: "
            f"{type(statement).__name__}"
        )

    def _compile_action(
        self,
        *,
        prefix: str,
        kind: NodeKind,
        expression: Expression,
    ) -> tuple[str, ...]:
        node_id = self._fresh_id(prefix)
        value = self._try_value(expression)
        self._add_node(
            GraphNode(
                id=node_id,
                kind=kind,
                label=prefix,
                value=value,
                metadata=self._expression_metadata(expression),
            )
        )
        self._add_expression_dependencies(expression, node_id)
        return (node_id,)


def compile_program(program: Program) -> CompileResult:
    if not isinstance(program, Program):
        raise TypeError("compile_program requires a Program")

    diagnostics = _semantic_diagnostics(program)
    if diagnostics:
        return CompileResult(graph=None, diagnostics=diagnostics)

    graph = _GraphBuilder().build(program)
    return CompileResult(graph=graph, diagnostics=())


def compile_ast_to_execution_graph(program: Program) -> ExecutionGraph:
    result = compile_program(program)
    if not result.ok or result.graph is None:
        raise CompilationError(result.diagnostics)
    return result.graph
