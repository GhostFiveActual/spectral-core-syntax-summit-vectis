from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from vectis.ast import (
    AnalyzeDeclaration,
    Block,
    BooleanLiteral,
    CitationsStatement,
    Expression,
    Mission,
    NumberLiteral,
    Program,
    PublishStatement,
    Reference,
    RequestStatement,
    RequireStatement,
    SourceDeclaration,
    StringLiteral,
    UnaryExpression,
    BinaryExpression,
    WhenStatement,  # Added import for WhenStatement
)
from vectis.diagnostic import (
    DiagnosticCode,
    DiagnosticError,
    error_diagnostic,
    point_span,
)
from vectis.source_position import SourcePosition
from vectis.source_span import SourceSpan


class SemanticError(DiagnosticError):
    """Compatibility wrapper for semantic diagnostics."""

    def __init__(self, message: str, *, span: SourceSpan) -> None:
        diagnostic = error_diagnostic(
            code=DiagnosticCode.LEX_UNRECOGNIZED_CHARACTER,
            message=message,
            span=span,
        )
        super().__init__(diagnostic)


class SemanticAnalyzer:
    def __init__(self, program: Program) -> None:
        self.program = program
        self.declarations: Dict[str, Expression] = {}

    def analyze(self) -> List[Diagnostic]:
        diagnostics = []
        for statement in self.program.statements:
            diagnostics.extend(self._analyze_statement(statement))
        return diagnostics

    def _analyze_statement(self, statement: Statement) -> List[Diagnostic]:
        if isinstance(statement, Mission):
            return self._analyze_mission(statement)
        elif isinstance(statement, SourceDeclaration):
            return self._analyze_source_declaration(statement)
        elif isinstance(statement, AnalyzeDeclaration):
            return self._analyze_analyze_declaration(statement)
        elif isinstance(statement, RequireStatement):
            return self._analyze_require_statement(statement)
        elif isinstance(statement, RequestStatement):
            return self._analyze_request_statement(statement)
        elif isinstance(statement, PublishStatement):
            return self._analyze_publish_statement(statement)
        elif isinstance(statement, CitationsStatement):
            return self._analyze_citations_statement(statement)
        elif isinstance(statement, WhenStatement):
            return self._analyze_when_statement(statement)
        else:
            return [SemanticError(
                f"Unhandled statement type: {type(statement).__name__}",
                span=statement.span,
            )]

    def _analyze_mission(self, mission: Mission) -> List[Diagnostic]:
        return self._analyze_block(mission.body)

    def _analyze_source_declaration(self, declaration: SourceDeclaration) -> List[Diagnostic]:
        if declaration.name in self.declarations:
            return [SemanticError(
                f"Duplicate declaration: {declaration.name}",
                span=declaration.span,
            )]
        self.declarations[declaration.name] = declaration.value
        return []

    def _analyze_analyze_declaration(self, declaration: AnalyzeDeclaration) -> List[Diagnostic]:
        if declaration.name in self.declarations:
            return [SemanticError(
                f"Duplicate declaration: {declaration.name}",
                span=declaration.span,
            )]
        if declaration.value is not None:
            return self._analyze_expression(declaration.value)
        return []

    def _analyze_require_statement(self, statement: RequireStatement) -> List[Diagnostic]:
        return self._analyze_expression(statement.capability)

    def _analyze_request_statement(self, statement: RequestStatement) -> List[Diagnostic]:
        return self._analyze_expression(statement.capability)

    def _analyze_publish_statement(self, statement: PublishStatement) -> List[Diagnostic]:
        return self._analyze_expression(statement.value)

    def _analyze_citations_statement(self, statement: CitationsStatement) -> List[Diagnostic]:
        diagnostics = []
        for citation in statement.values:
            diagnostics.extend(self._analyze_expression(citation))
        return diagnostics

    def _analyze_when_statement(self, statement: WhenStatement) -> List[Diagnostic]:
        diagnostics = self._analyze_expression(statement.condition)
        diagnostics.extend(self._analyze_block(statement.body))
        if statement.otherwise is not None:
            diagnostics.extend(self._analyze_block(statement.otherwise))
        return diagnostics

    def _analyze_block(self, block: Block) -> List[Diagnostic]:
        diagnostics = []
        for statement in block.statements:
            diagnostics.extend(self._analyze_statement(statement))
        return diagnostics

    def _analyze_expression(self, expression: Expression) -> List[Diagnostic]:
        diagnostics = []
        if isinstance(expression, Reference):
            if expression.name not in self.declarations:
                diagnostics.append(SemanticError(
                    f"Undeclared reference: {expression.name}",
                    span=expression.span,
                ))
        elif isinstance(expression, BinaryExpression):
            diagnostics.extend(self._analyze_expression(expression.left))
            diagnostics.extend(self._analyze_expression(expression.right))
        elif isinstance(expression, UnaryExpression):
            diagnostics.extend(self._analyze_expression(expression.operand))
        elif isinstance(expression, StringLiteral):
            pass
        elif isinstance(expression, NumberLiteral):
            pass
        elif isinstance(expression, BooleanLiteral):
            pass
        else:
            diagnostics.append(SemanticError(
                f"Unhandled expression type: {type(expression).__name__}",
                span=expression.span,
            ))
        return diagnostics

    def _error(self, message: str, span: SourceSpan) -> None:
        diagnostic = error_diagnostic(
            code=DiagnosticCode.LEX_UNRECOGNIZED_CHARACTER,
            message=message,
            span=span,
        )
        raise DiagnosticError(diagnostic)


class ValueType:
    pass

class SemanticResult:
    pass

def analyze(program: Program) -> List[Diagnostic]:
    analyzer = SemanticAnalyzer(program)
    return analyzer.analyze()
