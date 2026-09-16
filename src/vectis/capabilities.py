from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from vectis.ast import (
    AnalyzeDeclaration,
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
    StringLiteral,
    UnaryExpression,
    BinaryExpression,
    WhenStatement,
)
from vectis.ir import EdgeKind, GraphEdge, GraphNode, NodeKind, ExecutionGraph
from vectis.diagnostic import DiagnosticCode, DiagnosticError, error_diagnostic, point_span
from vectis.source_position import SourcePosition
from vectis.source_span import SourceSpan


class CapabilityError(DiagnosticError):
    """Base class for capability-related errors."""

    def __init__(self, message: str, *, span: SourceSpan) -> None:
        diagnostic = error_diagnostic(
            code=DiagnosticCode.LEX_UNRECOGNIZED_CHARACTER,
            message=message,
            span=span,
        )
        super().__init__(diagnostic)


class Capability:
    def __init__(self, name: str, description: str, required: bool = False, optional: bool = False):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Capability name must be a non-empty string")
        if not isinstance(description, str) or not description.strip():
            raise ValueError("Capability description must be a non-empty string")
        if required and optional:
            raise ValueError("A capability cannot be both required and optional")
        self.name = name
        self.description = description
        self.required = required
        self.optional = optional

    def __repr__(self) -> str:
        return f"Capability(name={self.name}, description={self.description}, required={self.required}, optional={self.optional})"


class CapabilityRegistry:
    def __init__(self):
        self.capabilities: Dict[str, Capability] = {}
        self.declared_capabilities: Dict[str, Capability] = {}

    def declare_capability(self, capability: Capability) -> None:
        if not isinstance(capability, Capability):
            raise TypeError("Only Capability instances can be declared")
        if capability.name in self.capabilities:
            raise ValueError(f"Capability '{capability.name}' already declared")
        self.capabilities[capability.name] = capability
        self.declared_capabilities[capability.name] = capability

    def get_capability(self, name: str) -> Optional[Capability]:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Capability name must be a non-empty string")
        return self.capabilities.get(name)

    def has_capability(self, name: str) -> bool:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Capability name must be a non-empty string")
        return name in self.capabilities

    def check_capabilities(self, execution_graph: ExecutionGraph) -> List[DiagnosticError]:
        diagnostics = []
        for node in execution_graph.nodes:
            for key, value in node.metadata:
                if key in self.declared_capabilities:
                    capability = self.declared_capabilities[key]
                    if capability.required and value is None:
                        diagnostics.append(CapabilityDenied(
                            f"Required capability '{key}' is unavailable",
                            span=point_span(
                                file="<capability>",
                                line=1,
                                column=1,
                            ),
                        ))
                    elif capability.optional and value is None:
                        continue
                    else:
                        if not isinstance(value, (str, int, float, bool, type(None))):
                            diagnostics.append(CapabilityError(
                                f"Invalid value for capability '{key}': {value}",
                                span=point_span(
                                file="<capability>",
                                line=1,
                                column=1,
                            ),
                            ))
        return diagnostics


class CapabilityChecker:
    def __init__(self, model: CapabilityRegistry):
        self.model = model

    def check(self, execution_graph: ExecutionGraph) -> List[DiagnosticError]:
        return self.model.check_capabilities(execution_graph)


class CapabilityResolver:
    def __init__(self, model: CapabilityRegistry):
        self.model = model

    def resolve(self, execution_graph: ExecutionGraph) -> Dict[str, Any]:
        result = {}
        for node in execution_graph.nodes:
            for key, value in node.metadata:
                if key in self.model.declared_capabilities:
                    capability = self.model.declared_capabilities[key]
                    if capability.required and value is None:
                        result[key] = None
                    else:
                        result[key] = value
        return result

# ---------------------------------------------------------------------------
# RUN-001 public compatibility surface
# ---------------------------------------------------------------------------

class CapabilityDenied(CapabilityError):
    """Raised when an unavailable capability is denied."""


# Backward-compatible name retained for the capability model API established
# by the RUN-001 test surface. CapabilityRegistry is the canonical class.
CapabilityModel = CapabilityRegistry
