# GHOST FIVE // SPECTRAL CORE // VECTIS
# Evaluates deterministic VECTIS expressions and pure built in functions.
"""Deterministic pure expression evaluation for VECTIS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from vectis.ast import (
    BinaryExpression,
    BooleanLiteral,
    CallExpression,
    Expression,
    NumberLiteral,
    Reference,
    StringLiteral,
    UnaryExpression,
)

Scalar = str | int | float | bool | None
BuiltinHandler = Callable[[tuple[Scalar, ...]], Scalar]


class EvaluationError(ValueError):
    """Raised when a deterministic expression cannot be evaluated."""


@dataclass(frozen=True, slots=True)
class BuiltinFunction:
    name: str
    description: str
    min_args: int
    max_args: int | None
    handler: BuiltinHandler

    def validate_arity(self, count: int) -> None:
        if count < self.min_args:
            raise EvaluationError(
                f"{self.name}() expects at least {self.min_args} arguments"
            )
        if self.max_args is not None and count > self.max_args:
            raise EvaluationError(
                f"{self.name}() expects at most {self.max_args} arguments"
            )


def _require_text(value: Scalar, name: str) -> str:
    if not isinstance(value, str):
        raise EvaluationError(f"{name}() expects string arguments")
    return value


def _require_number(value: Scalar, name: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvaluationError(f"{name}() expects numeric arguments")
    return value


def _upper(args: tuple[Scalar, ...]) -> Scalar:
    return _require_text(args[0], "upper").upper()


def _lower(args: tuple[Scalar, ...]) -> Scalar:
    return _require_text(args[0], "lower").lower()


def _trim(args: tuple[Scalar, ...]) -> Scalar:
    return _require_text(args[0], "trim").strip()


def _length(args: tuple[Scalar, ...]) -> Scalar:
    return len(_require_text(args[0], "length"))


def _concat(args: tuple[Scalar, ...]) -> Scalar:
    return "".join(str(item) for item in args)


def _contains(args: tuple[Scalar, ...]) -> Scalar:
    return _require_text(args[1], "contains") in _require_text(
        args[0], "contains"
    )


def _starts_with(args: tuple[Scalar, ...]) -> Scalar:
    return _require_text(args[0], "starts_with").startswith(
        _require_text(args[1], "starts_with")
    )


def _ends_with(args: tuple[Scalar, ...]) -> Scalar:
    return _require_text(args[0], "ends_with").endswith(
        _require_text(args[1], "ends_with")
    )


def _capitalize(args: tuple[Scalar, ...]) -> Scalar:
    return _require_text(args[0], "capitalize").capitalize()


def _title(args: tuple[Scalar, ...]) -> Scalar:
    return _require_text(args[0], "title").title()


def _replace(args: tuple[Scalar, ...]) -> Scalar:
    text = _require_text(args[0], "replace")
    old = _require_text(args[1], "replace")
    new = _require_text(args[2], "replace")
    return text.replace(old, new)


def _repeat(args: tuple[Scalar, ...]) -> Scalar:
    text = _require_text(args[0], "repeat")
    count = _require_number(args[1], "repeat")
    if not isinstance(count, int):
        raise EvaluationError("repeat() count must be an integer")
    if not 0 <= count <= 1000:
        raise EvaluationError("repeat() count must be between 0 and 1000")
    return text * count


def _clamp(args: tuple[Scalar, ...]) -> Scalar:
    value = _require_number(args[0], "clamp")
    low = _require_number(args[1], "clamp")
    high = _require_number(args[2], "clamp")
    if low > high:
        raise EvaluationError("clamp() minimum cannot exceed maximum")
    return max(low, min(value, high))


def _between(args: tuple[Scalar, ...]) -> Scalar:
    value = _require_number(args[0], "between")
    low = _require_number(args[1], "between")
    high = _require_number(args[2], "between")
    if low > high:
        raise EvaluationError("between() minimum cannot exceed maximum")
    return low <= value <= high


def _if_else(args: tuple[Scalar, ...]) -> Scalar:
    condition = args[0]
    if not isinstance(condition, bool):
        raise EvaluationError("if_else() condition must be boolean")
    return args[1] if condition else args[2]


def _abs(args: tuple[Scalar, ...]) -> Scalar:
    return abs(_require_number(args[0], "abs"))


def _round(args: tuple[Scalar, ...]) -> Scalar:
    value = _require_number(args[0], "round")
    if len(args) == 1:
        return round(value)
    digits = _require_number(args[1], "round")
    if not isinstance(digits, int):
        raise EvaluationError("round() digits must be an integer")
    return round(value, digits)


def _min(args: tuple[Scalar, ...]) -> Scalar:
    values = tuple(_require_number(item, "min") for item in args)
    return min(values)


def _max(args: tuple[Scalar, ...]) -> Scalar:
    values = tuple(_require_number(item, "max") for item in args)
    return max(values)


def _string(args: tuple[Scalar, ...]) -> Scalar:
    value = args[0]
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _number(args: tuple[Scalar, ...]) -> Scalar:
    value = args[0]
    if isinstance(value, bool):
        raise EvaluationError("number() does not convert booleans")
    if isinstance(value, (int, float)):
        return value
    text = _require_text(value, "number").strip()
    try:
        return float(text) if "." in text else int(text)
    except ValueError as exc:
        raise EvaluationError(f"number() cannot parse {text!r}") from exc


def _boolean(args: tuple[Scalar, ...]) -> Scalar:
    value = args[0]
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value != 0
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1", "on"}:
            return True
        if lowered in {"false", "no", "0", "off", ""}:
            return False
    raise EvaluationError(f"boolean() cannot convert {value!r}")


BUILTINS: dict[str, BuiltinFunction] = {
    item.name: item
    for item in (
        BuiltinFunction("upper", "Uppercase a string.", 1, 1, _upper),
        BuiltinFunction("lower", "Lowercase a string.", 1, 1, _lower),
        BuiltinFunction("trim", "Trim surrounding whitespace.", 1, 1, _trim),
        BuiltinFunction("length", "Return string length.", 1, 1, _length),
        BuiltinFunction("concat", "Concatenate scalar values.", 1, None, _concat),
        BuiltinFunction("contains", "Test whether text contains a substring.", 2, 2, _contains),
        BuiltinFunction("starts_with", "Test a string prefix.", 2, 2, _starts_with),
        BuiltinFunction("ends_with", "Test a string suffix.", 2, 2, _ends_with),
        BuiltinFunction("capitalize", "Capitalize text.", 1, 1, _capitalize),
        BuiltinFunction("title", "Convert text to title case.", 1, 1, _title),
        BuiltinFunction("replace", "Replace text deterministically.", 3, 3, _replace),
        BuiltinFunction("repeat", "Repeat text a bounded number of times.", 2, 2, _repeat),
        BuiltinFunction("clamp", "Clamp a number to an inclusive range.", 3, 3, _clamp),
        BuiltinFunction("between", "Test an inclusive numeric range.", 3, 3, _between),
        BuiltinFunction("if_else", "Select one of two scalar values.", 3, 3, _if_else),
        BuiltinFunction("abs", "Return absolute numeric value.", 1, 1, _abs),
        BuiltinFunction("round", "Round a number, optionally to digits.", 1, 2, _round),
        BuiltinFunction("min", "Return the minimum numeric value.", 1, None, _min),
        BuiltinFunction("max", "Return the maximum numeric value.", 1, None, _max),
        BuiltinFunction("string", "Convert a scalar to text.", 1, 1, _string),
        BuiltinFunction("number", "Convert text to a number.", 1, 1, _number),
        BuiltinFunction("boolean", "Convert a scalar to boolean.", 1, 1, _boolean),
    )
}


def builtin_manifest() -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "name": item.name,
            "description": item.description,
            "min_args": item.min_args,
            "max_args": item.max_args,
        }
        for item in sorted(BUILTINS.values(), key=lambda item: item.name)
    )


def evaluate_expression(
    expression: Expression,
    values: Mapping[str, Scalar] | None = None,
) -> Scalar:
    """Evaluate one pure expression using an explicit value environment."""
    env = values or {}

    if isinstance(expression, StringLiteral):
        return expression.value
    if isinstance(expression, NumberLiteral):
        return expression.value
    if isinstance(expression, BooleanLiteral):
        return expression.value
    if isinstance(expression, Reference):
        if expression.name not in env:
            raise EvaluationError(
                f"Reference {expression.name!r} has no runtime value"
            )
        return env[expression.name]
    if isinstance(expression, CallExpression):
        function = BUILTINS.get(expression.name)
        if function is None:
            raise EvaluationError(
                f"Unknown built-in function {expression.name!r}"
            )
        function.validate_arity(len(expression.arguments))
        arguments = tuple(
            evaluate_expression(argument, env)
            for argument in expression.arguments
        )
        return function.handler(arguments)
    if isinstance(expression, UnaryExpression):
        value = evaluate_expression(expression.operand, env)
        if expression.operator == "!":
            if not isinstance(value, bool):
                raise EvaluationError("'!' expects a boolean operand")
            return not value
        if expression.operator in {"+", "-"}:
            number = _require_number(value, expression.operator)
            return +number if expression.operator == "+" else -number
        raise EvaluationError(f"Unsupported unary operator {expression.operator!r}")
    if isinstance(expression, BinaryExpression):
        left = evaluate_expression(expression.left, env)
        right = evaluate_expression(expression.right, env)
        operator = expression.operator

        if operator == "&&":
            if not isinstance(left, bool) or not isinstance(right, bool):
                raise EvaluationError("'&&' expects boolean operands")
            return left and right
        if operator == "||":
            if not isinstance(left, bool) or not isinstance(right, bool):
                raise EvaluationError("'||' expects boolean operands")
            return left or right
        if operator in {"==", "!="}:
            result = left == right
            return result if operator == "==" else not result
        if operator in {">", ">=", "<", "<="}:
            if type(left) is not type(right) and not (
                isinstance(left, (int, float))
                and not isinstance(left, bool)
                and isinstance(right, (int, float))
                and not isinstance(right, bool)
            ):
                raise EvaluationError(
                    f"{operator!r} expects comparable operands"
                )
            if operator == ">":
                return left > right
            if operator == ">=":
                return left >= right
            if operator == "<":
                return left < right
            return left <= right
        if operator == "+":
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            return _require_number(left, "+") + _require_number(right, "+")
        if operator == "-":
            return _require_number(left, "-") - _require_number(right, "-")
        if operator == "*":
            return _require_number(left, "*") * _require_number(right, "*")
        if operator == "/":
            divisor = _require_number(right, "/")
            if divisor == 0:
                raise EvaluationError("division by zero")
            return _require_number(left, "/") / divisor
        if operator == "%":
            divisor = _require_number(right, "%")
            if divisor == 0:
                raise EvaluationError("modulo by zero")
            return _require_number(left, "%") % divisor

        raise EvaluationError(f"Unsupported binary operator {operator!r}")

    raise EvaluationError(
        f"Unsupported expression type {type(expression).__name__}"
    )
