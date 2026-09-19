"""Semantic analysis for VECTIS programs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

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
from vectis.diagnostic import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticError,
    error_diagnostic,
)
from vectis.evaluator import BUILTINS
from vectis.source_span import SourceSpan


class SemanticError(DiagnosticError):
    """Compatibility exception for callers that require raised semantics."""

    def __init__(
        self,
        message: str,
        *,
        span: SourceSpan,
        code: DiagnosticCode = DiagnosticCode.SEM_TYPE_MISMATCH,
    ) -> None:
        super().__init__(
            error_diagnostic(
                code=code,
                message=message,
                span=span,
            )
        )


class ValueType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SemanticResult:
    diagnostics: tuple[Diagnostic, ...]
    declarations: tuple[tuple[str, ValueType], ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


_BUILTIN_RESULTS: dict[str, ValueType] = {
    "upper": ValueType.STRING,
    "lower": ValueType.STRING,
    "trim": ValueType.STRING,
    "length": ValueType.NUMBER,
    "concat": ValueType.STRING,
    "contains": ValueType.BOOLEAN,
    "starts_with": ValueType.BOOLEAN,
    "ends_with": ValueType.BOOLEAN,
    "abs": ValueType.NUMBER,
    "round": ValueType.NUMBER,
    "min": ValueType.NUMBER,
    "max": ValueType.NUMBER,
    "string": ValueType.STRING,
    "number": ValueType.NUMBER,
    "boolean": ValueType.BOOLEAN,
}


class SemanticAnalyzer:
    def __init__(self, program: Program) -> None:
        if not isinstance(program, Program):
            raise TypeError("program must be Program")
        self.program = program
        self.declarations: dict[str, ValueType] = {}

    def analyze(self) -> list[Diagnostic]:
        return list(self.result().diagnostics)

    def result(self) -> SemanticResult:
        diagnostics: list[Diagnostic] = []
        for statement in self.program.statements:
            diagnostics.extend(self._analyze_statement(statement))
        return SemanticResult(
            diagnostics=tuple(diagnostics),
            declarations=tuple(self.declarations.items()),
        )

    def _diagnostic(
        self,
        code: DiagnosticCode,
        message: str,
        span: SourceSpan,
    ) -> Diagnostic:
        return error_diagnostic(code=code, message=message, span=span)

    def _declare(
        self,
        name: str,
        value_type: ValueType,
        span: SourceSpan,
    ) -> list[Diagnostic]:
        if name in self.declarations:
            return [
                self._diagnostic(
                    DiagnosticCode.SEM_DUPLICATE_DECLARATION,
                    f"Duplicate declaration: {name}",
                    span,
                )
            ]
        self.declarations[name] = value_type
        return []

    def _analyze_statement(self, statement: Statement) -> list[Diagnostic]:
        if isinstance(statement, Mission):
            return self._analyze_block(statement.body)

        if isinstance(statement, (SourceDeclaration, LetDeclaration)):
            diagnostics = self._analyze_expression(statement.value)
            value_type = self._infer_type(statement.value)
            diagnostics.extend(
                self._declare(statement.name, value_type, statement.span)
            )
            return diagnostics

        if isinstance(statement, AnalyzeDeclaration):
            diagnostics: list[Diagnostic] = []
            value_type = ValueType.UNKNOWN
            if statement.value is not None:
                diagnostics.extend(self._analyze_expression(statement.value))
                value_type = self._infer_type(statement.value)
            diagnostics.extend(
                self._declare(statement.name, value_type, statement.span)
            )
            return diagnostics

        if isinstance(statement, RequireStatement):
            return self._analyze_expression(statement.capability)
        if isinstance(statement, RequestStatement):
            return self._analyze_expression(statement.capability)
        if isinstance(statement, AssertStatement):
            diagnostics = self._analyze_expression(statement.condition)
            condition_type = self._infer_type(statement.condition)
            if condition_type not in (ValueType.BOOLEAN, ValueType.UNKNOWN):
                diagnostics.append(
                    self._diagnostic(
                        DiagnosticCode.SEM_TYPE_MISMATCH,
                        "assert condition must evaluate to boolean",
                        statement.condition.span,
                    )
                )
            return diagnostics
        if isinstance(statement, PublishStatement):
            return self._analyze_expression(statement.value)
        if isinstance(statement, ConfidenceStatement):
            diagnostics = self._analyze_expression(statement.value)
            value_type = self._infer_type(statement.value)
            if value_type not in (ValueType.NUMBER, ValueType.UNKNOWN):
                diagnostics.append(
                    self._diagnostic(
                        DiagnosticCode.SEM_TYPE_MISMATCH,
                        "confidence must evaluate to a number",
                        statement.value.span,
                    )
                )
            return diagnostics
        if isinstance(statement, CitationsStatement):
            diagnostics: list[Diagnostic] = []
            for value in statement.values:
                diagnostics.extend(self._analyze_expression(value))
            return diagnostics
        if isinstance(statement, WhenStatement):
            diagnostics = self._analyze_expression(statement.condition)
            condition_type = self._infer_type(statement.condition)
            if condition_type not in (ValueType.BOOLEAN, ValueType.UNKNOWN):
                diagnostics.append(
                    self._diagnostic(
                        DiagnosticCode.SEM_TYPE_MISMATCH,
                        "when condition must evaluate to boolean",
                        statement.condition.span,
                    )
                )
            diagnostics.extend(self._analyze_block(statement.body))
            if statement.otherwise is not None:
                diagnostics.extend(self._analyze_block(statement.otherwise))
            return diagnostics

        return [
            self._diagnostic(
                DiagnosticCode.SEM_TYPE_MISMATCH,
                f"Unhandled statement type: {type(statement).__name__}",
                statement.span,
            )
        ]

    def _analyze_block(self, block: Block) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        for statement in block.statements:
            diagnostics.extend(self._analyze_statement(statement))
        return diagnostics

    def _analyze_expression(self, expression: Expression) -> list[Diagnostic]:
        if isinstance(expression, Reference):
            if expression.name not in self.declarations:
                return [
                    self._diagnostic(
                        DiagnosticCode.SEM_UNDECLARED_REFERENCE,
                        f"Undeclared reference: {expression.name}",
                        expression.span,
                    )
                ]
            return []

        if isinstance(expression, CallExpression):
            diagnostics: list[Diagnostic] = []
            function = BUILTINS.get(expression.name)
            if function is None:
                diagnostics.append(
                    self._diagnostic(
                        DiagnosticCode.SEM_UNKNOWN_FUNCTION,
                        f"Unknown built-in function: {expression.name}",
                        expression.span,
                    )
                )
            else:
                count = len(expression.arguments)
                if count < function.min_args or (
                    function.max_args is not None and count > function.max_args
                ):
                    diagnostics.append(
                        self._diagnostic(
                            DiagnosticCode.SEM_INVALID_ARITY,
                            f"Invalid argument count for {expression.name}()",
                            expression.span,
                        )
                    )
            for argument in expression.arguments:
                diagnostics.extend(self._analyze_expression(argument))
            return diagnostics

        if isinstance(expression, BinaryExpression):
            return [
                *self._analyze_expression(expression.left),
                *self._analyze_expression(expression.right),
            ]

        if isinstance(expression, UnaryExpression):
            return self._analyze_expression(expression.operand)

        if isinstance(
            expression,
            (StringLiteral, NumberLiteral, BooleanLiteral),
        ):
            return []

        return [
            self._diagnostic(
                DiagnosticCode.SEM_TYPE_MISMATCH,
                f"Unhandled expression type: {type(expression).__name__}",
                expression.span,
            )
        ]

    def _infer_type(self, expression: Expression) -> ValueType:
        if isinstance(expression, StringLiteral):
            return ValueType.STRING
        if isinstance(expression, NumberLiteral):
            return ValueType.NUMBER
        if isinstance(expression, BooleanLiteral):
            return ValueType.BOOLEAN
        if isinstance(expression, Reference):
            return self.declarations.get(expression.name, ValueType.UNKNOWN)
        if isinstance(expression, CallExpression):
            return _BUILTIN_RESULTS.get(expression.name, ValueType.UNKNOWN)
        if isinstance(expression, UnaryExpression):
            if expression.operator == "!":
                return ValueType.BOOLEAN
            return ValueType.NUMBER
        if isinstance(expression, BinaryExpression):
            if expression.operator in {
                "&&",
                "||",
                "==",
                "!=",
                ">",
                ">=",
                "<",
                "<=",
            }:
                return ValueType.BOOLEAN
            if expression.operator == "+":
                left = self._infer_type(expression.left)
                right = self._infer_type(expression.right)
                if left is ValueType.STRING and right is ValueType.STRING:
                    return ValueType.STRING
                if left is ValueType.NUMBER and right is ValueType.NUMBER:
                    return ValueType.NUMBER
                return ValueType.UNKNOWN
            if expression.operator in {"-", "*", "/", "%"}:
                return ValueType.NUMBER
        return ValueType.UNKNOWN


def analyze_result(program: Program) -> SemanticResult:
    return SemanticAnalyzer(program).result()


def analyze(program: Program) -> list[Diagnostic]:
    return SemanticAnalyzer(program).analyze()
