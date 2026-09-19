"""Typed abstract syntax tree for the VECTIS language."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from vectis.source_span import SourceSpan


@dataclass(frozen=True, slots=True, kw_only=True)
class Node:
    """Base class for every VECTIS AST node."""

    span: SourceSpan

    def __post_init__(self) -> None:
        if not isinstance(self.span, SourceSpan):
            raise TypeError("span must be a SourceSpan")


@dataclass(frozen=True, slots=True, kw_only=True)
class Expression(Node):
    """Base class for value-producing syntax."""


@dataclass(frozen=True, slots=True, kw_only=True)
class Statement(Node):
    """Base class for executable or declarative syntax."""


@dataclass(frozen=True, slots=True, kw_only=True)
class StringLiteral(Expression):
    value: str

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        if not isinstance(self.value, str):
            raise TypeError("StringLiteral.value must be str")


@dataclass(frozen=True, slots=True, kw_only=True)
class NumberLiteral(Expression):
    value: int | float

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        if isinstance(self.value, bool) or not isinstance(
            self.value,
            (int, float),
        ):
            raise TypeError("NumberLiteral.value must be int or float")


@dataclass(frozen=True, slots=True, kw_only=True)
class BooleanLiteral(Expression):
    value: bool

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        if not isinstance(self.value, bool):
            raise TypeError("BooleanLiteral.value must be bool")


@dataclass(frozen=True, slots=True, kw_only=True)
class Reference(Expression):
    name: str

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        _require_name(self.name, "Reference.name")


@dataclass(frozen=True, slots=True, kw_only=True)
class CallExpression(Expression):
    """Call one deterministic built-in function."""

    name: str
    arguments: tuple[Expression, ...] = ()

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        _require_name(self.name, "CallExpression.name")
        if not isinstance(self.arguments, tuple):
            raise TypeError("CallExpression.arguments must be tuple")
        if not all(isinstance(item, Expression) for item in self.arguments):
            raise TypeError(
                "CallExpression.arguments must contain only Expressions"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class UnaryExpression(Expression):
    operator: str
    operand: Expression

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        if not isinstance(self.operator, str) or not self.operator:
            raise ValueError("UnaryExpression.operator must not be empty")
        if not isinstance(self.operand, Expression):
            raise TypeError("UnaryExpression.operand must be Expression")


@dataclass(frozen=True, slots=True, kw_only=True)
class BinaryExpression(Expression):
    left: Expression
    operator: str
    right: Expression

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        if not isinstance(self.left, Expression):
            raise TypeError("BinaryExpression.left must be Expression")
        if not isinstance(self.operator, str) or not self.operator:
            raise ValueError("BinaryExpression.operator must not be empty")
        if not isinstance(self.right, Expression):
            raise TypeError("BinaryExpression.right must be Expression")


@dataclass(frozen=True, slots=True, kw_only=True)
class Block(Node):
    statements: tuple[Statement, ...] = ()

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        if not isinstance(self.statements, tuple):
            raise TypeError("Block.statements must be tuple")
        if not all(
            isinstance(statement, Statement)
            for statement in self.statements
        ):
            raise TypeError(
                "Block.statements must contain only Statement nodes"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class Mission(Statement):
    name: str
    body: Block

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        _require_name(self.name, "Mission.name")
        if not isinstance(self.body, Block):
            raise TypeError("Mission.body must be Block")


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceDeclaration(Statement):
    name: str
    value: Expression

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        _require_name(self.name, "SourceDeclaration.name")
        if not isinstance(self.value, Expression):
            raise TypeError("SourceDeclaration.value must be Expression")


@dataclass(frozen=True, slots=True, kw_only=True)
class LetDeclaration(Statement):
    """Declare a deterministic computed value."""

    name: str
    value: Expression

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        _require_name(self.name, "LetDeclaration.name")
        if not isinstance(self.value, Expression):
            raise TypeError("LetDeclaration.value must be Expression")


@dataclass(frozen=True, slots=True, kw_only=True)
class AnalyzeDeclaration(Statement):
    name: str
    value: Expression | None = None

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        _require_name(self.name, "AnalyzeDeclaration.name")
        if self.value is not None and not isinstance(
            self.value,
            Expression,
        ):
            raise TypeError(
                "AnalyzeDeclaration.value must be Expression or None"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class RequireStatement(Statement):
    capability: Expression

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        if not isinstance(self.capability, Expression):
            raise TypeError(
                "RequireStatement.capability must be Expression"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class RequestStatement(Statement):
    capability: Expression

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        if not isinstance(self.capability, Expression):
            raise TypeError(
                "RequestStatement.capability must be Expression"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class AssertStatement(Statement):
    condition: Expression

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        if not isinstance(self.condition, Expression):
            raise TypeError(
                "AssertStatement.condition must be Expression"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class PublishStatement(Statement):
    value: Expression

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        if not isinstance(self.value, Expression):
            raise TypeError(
                "PublishStatement.value must be Expression"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class CitationsStatement(Statement):
    values: tuple[Expression, ...]

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        if not isinstance(self.values, tuple):
            raise TypeError("CitationsStatement.values must be tuple")
        if not all(
            isinstance(value, Expression)
            for value in self.values
        ):
            raise TypeError(
                "CitationsStatement.values must contain Expressions"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class ConfidenceStatement(Statement):
    value: Expression

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        if not isinstance(self.value, Expression):
            raise TypeError(
                "ConfidenceStatement.value must be Expression"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class WhenStatement(Statement):
    condition: Expression
    body: Block
    otherwise: Block | None = None

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        if not isinstance(self.condition, Expression):
            raise TypeError(
                "WhenStatement.condition must be Expression"
            )
        if not isinstance(self.body, Block):
            raise TypeError("WhenStatement.body must be Block")
        if self.otherwise is not None and not isinstance(
            self.otherwise,
            Block,
        ):
            raise TypeError(
                "WhenStatement.otherwise must be Block or None"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class Program(Node):
    statements: tuple[Statement, ...] = ()

    def __post_init__(self) -> None:
        Node.__post_init__(self)
        if not isinstance(self.statements, tuple):
            raise TypeError("Program.statements must be tuple")
        if not all(
            isinstance(statement, Statement)
            for statement in self.statements
        ):
            raise TypeError(
                "Program.statements must contain only Statement nodes"
            )


Literal: TypeAlias = StringLiteral | NumberLiteral | BooleanLiteral


def _require_name(value: object, label: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be str")
    if not value:
        raise ValueError(f"{label} must not be empty")
