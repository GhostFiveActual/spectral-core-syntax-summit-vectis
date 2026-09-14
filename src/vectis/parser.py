from __future__ import annotations

from dataclasses import replace

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
    StringLiteral,
    UnaryExpression,
    WhenStatement,
)
from vectis.lexer import Lexer
from vectis.source_position import SourcePosition
from vectis.source_span import SourceSpan
from vectis.token import Token


class ParserError(ValueError):
    def __init__(self, message: str, *, file: str, line: int, column: int) -> None:
        self.message = message
        self.file = file
        self.line = line
        self.column = column
        super().__init__(f"{file}:{line}:{column}: {message}")


class Parser:
    _BINARY_LEVELS = (
        ("||",),
        ("&&",),
        ("==", "!="),
        (">=", "<="),
        ("+", "-"),
        ("*", "/"),
    )
    _UNARY_OPERATORS = frozenset({"!", "+", "-"})

    def __init__(self, tokens: list[Token], *, file: str = "<memory>") -> None:
        if not isinstance(tokens, list):
            raise TypeError("tokens must be list[Token]")
        if not all(isinstance(token, Token) for token in tokens):
            raise TypeError("tokens must contain only Token instances")
        if not isinstance(file, str) or not file:
            raise ValueError("file must be a non-empty string")

        self.tokens = tokens
        self.file = file
        self.index = 0

    def parse_program(self) -> Program:
        statements = []

        while not self._at_end():
            statements.append(self._parse_statement())

        if statements:
            span = self._cover(statements[0].span, statements[-1].span)
        else:
            position = SourcePosition(line=1, column=1, file=self.file)
            span = SourceSpan(start=position, end=position)

        return Program(span=span, statements=tuple(statements))

    def _parse_statement(self):
        token = self._current()

        if token is None:
            self._error("expected statement")

        if token.type != "keyword":
            self._error(
                f"expected statement keyword, found {token.value!r}",
                token=token,
            )

        if token.value == "otherwise":
            self._error(
                "'otherwise' may only follow a 'when' block",
                token=token,
            )

        dispatch = {
            "mission": self._parse_mission,
            "source": self._parse_source,
            "analyze": self._parse_analyze,
            "require": self._parse_require,
            "request": self._parse_request,
            "publish": self._parse_publish,
            "citations": self._parse_citations,
            "confidence": self._parse_confidence,
            "when": self._parse_when,
        }

        parser = dispatch.get(token.value)

        if parser is None:
            self._error(
                f"keyword {token.value!r} cannot begin a statement",
                token=token,
            )

        return parser()

    def _parse_mission(self) -> Mission:
        start = self._expect("keyword", "mission")
        name = self._expect("string", description="mission name string")
        body = self._parse_block()
        return Mission(
            span=self._cover(start.span, body.span),
            name=name.value,
            body=body,
        )

    def _parse_source(self) -> SourceDeclaration:
        start = self._expect("keyword", "source")
        name = self._expect("identifier", description="source name")
        value = self._parse_expression()
        end = self._expect("punctuation", ";")
        return SourceDeclaration(
            span=self._cover(start.span, end.span),
            name=name.value,
            value=value,
        )

    def _parse_analyze(self) -> AnalyzeDeclaration:
        start = self._expect("keyword", "analyze")
        name = self._expect("identifier", description="analysis name")
        value = None if self._check("punctuation", ";") else self._parse_expression()
        end = self._expect("punctuation", ";")
        return AnalyzeDeclaration(
            span=self._cover(start.span, end.span),
            name=name.value,
            value=value,
        )

    def _parse_require(self) -> RequireStatement:
        start = self._expect("keyword", "require")
        capability = self._parse_expression()
        end = self._expect("punctuation", ";")
        return RequireStatement(
            span=self._cover(start.span, end.span),
            capability=capability,
        )

    def _parse_request(self) -> RequestStatement:
        start = self._expect("keyword", "request")
        capability = self._parse_expression()
        end = self._expect("punctuation", ";")
        return RequestStatement(
            span=self._cover(start.span, end.span),
            capability=capability,
        )

    def _parse_publish(self) -> PublishStatement:
        start = self._expect("keyword", "publish")
        value = self._parse_expression()
        end = self._expect("punctuation", ";")
        return PublishStatement(
            span=self._cover(start.span, end.span),
            value=value,
        )

    def _parse_confidence(self) -> ConfidenceStatement:
        start = self._expect("keyword", "confidence")
        value = self._parse_expression()
        end = self._expect("punctuation", ";")
        return ConfidenceStatement(
            span=self._cover(start.span, end.span),
            value=value,
        )

    def _parse_citations(self) -> CitationsStatement:
        start = self._expect("keyword", "citations")
        self._expect("punctuation", "[")
        values = []

        if not self._check("punctuation", "]"):
            values.append(self._parse_expression())

            while self._match("punctuation", ",") is not None:
                if self._check("punctuation", "]"):
                    self._error("expected expression after ','")
                values.append(self._parse_expression())

        self._expect("punctuation", "]")
        end = self._expect("punctuation", ";")
        return CitationsStatement(
            span=self._cover(start.span, end.span),
            values=tuple(values),
        )

    def _parse_when(self) -> WhenStatement:
        start = self._expect("keyword", "when")
        condition = self._parse_expression()
        body = self._parse_block()
        otherwise = None
        end_span = body.span

        if self._match("keyword", "otherwise") is not None:
            otherwise = self._parse_block()
            end_span = otherwise.span

        return WhenStatement(
            span=self._cover(start.span, end_span),
            condition=condition,
            body=body,
            otherwise=otherwise,
        )

    def _parse_block(self) -> Block:
        opening = self._expect("punctuation", "{")
        statements = []

        while not self._check("punctuation", "}"):
            if self._at_end():
                self._error("expected '}' to close block", token=opening)
            statements.append(self._parse_statement())

        closing = self._expect("punctuation", "}")
        return Block(
            span=self._cover(opening.span, closing.span),
            statements=tuple(statements),
        )

    def _parse_expression(self) -> Expression:
        return self._parse_binary_level(0)

    def _parse_binary_level(self, level: int) -> Expression:
        if level >= len(self._BINARY_LEVELS):
            return self._parse_unary()

        left = self._parse_binary_level(level + 1)
        operators = self._BINARY_LEVELS[level]

        while (
            self._current() is not None
            and self._current().type == "operator"
            and self._current().value in operators
        ):
            operator = self._advance()
            right = self._parse_binary_level(level + 1)
            left = BinaryExpression(
                span=self._cover(left.span, right.span),
                left=left,
                operator=operator.value,
                right=right,
            )

        return left

    def _parse_unary(self) -> Expression:
        token = self._current()

        if (
            token is not None
            and token.type == "operator"
            and token.value in self._UNARY_OPERATORS
        ):
            operator = self._advance()
            operand = self._parse_unary()
            return UnaryExpression(
                span=self._cover(operator.span, operand.span),
                operator=operator.value,
                operand=operand,
            )

        return self._parse_primary()

    def _parse_primary(self) -> Expression:
        token = self._current()

        if token is None:
            self._error("expected expression")

        if token.type == "string":
            self._advance()
            return StringLiteral(span=token.span, value=token.value)

        if token.type == "number":
            self._advance()
            value = float(token.value) if "." in token.value else int(token.value)
            return NumberLiteral(span=token.span, value=value)

        if token.type == "identifier":
            self._advance()

            if token.value == "true":
                return BooleanLiteral(span=token.span, value=True)

            if token.value == "false":
                return BooleanLiteral(span=token.span, value=False)

            return Reference(span=token.span, name=token.value)

        opening = self._match("punctuation", "(")

        if opening is not None:
            expression = self._parse_expression()
            closing = self._expect("punctuation", ")")
            return replace(
                expression,
                span=self._cover(opening.span, closing.span),
            )

        self._error(
            f"expected expression, found {token.value!r}",
            token=token,
        )

    def _at_end(self) -> bool:
        return self.index >= len(self.tokens)

    def _current(self) -> Token | None:
        return None if self._at_end() else self.tokens[self.index]

    def _advance(self) -> Token:
        token = self._current()

        if token is None:
            self._error("unexpected end of input")

        self.index += 1
        return token

    def _check(self, token_type: str, value: str | None = None) -> bool:
        token = self._current()

        if token is None or token.type != token_type:
            return False

        return value is None or token.value == value

    def _match(self, token_type: str, value: str | None = None) -> Token | None:
        if not self._check(token_type, value):
            return None

        return self._advance()

    def _expect(
        self,
        token_type: str,
        value: str | None = None,
        *,
        description: str | None = None,
    ) -> Token:
        if self._check(token_type, value):
            return self._advance()

        token = self._current()
        expected = description or (
            repr(value) if value is not None else token_type
        )

        if token is None:
            self._error(f"expected {expected}, found end of input")

        self._error(
            f"expected {expected}, found {token.value!r}",
            token=token,
        )

    def _error(self, message: str, *, token: Token | None = None) -> None:
        location = token if token is not None else self._current()

        if location is not None:
            position = location.span.start
        elif self.tokens:
            end = self.tokens[-1].span.end
            position = SourcePosition(
                line=end.line,
                column=end.column + 1,
                file=end.file,
            )
        else:
            position = SourcePosition(line=1, column=1, file=self.file)

        raise ParserError(
            message,
            file=position.file,
            line=position.line,
            column=position.column,
        )

    @staticmethod
    def _cover(first: SourceSpan, last: SourceSpan) -> SourceSpan:
        return SourceSpan(start=first.start, end=last.end)


def parse(source: str, file: str = "<memory>") -> Program:
    tokens = Lexer(source, file=file).tokenize()
    return Parser(tokens, file=file).parse_program()
