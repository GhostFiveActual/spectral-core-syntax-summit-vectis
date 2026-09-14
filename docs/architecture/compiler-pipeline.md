# Compiler Pipeline

## Source

Source locations must remain available through all compiler stages.

## Lexer

Characters become typed tokens with source spans.

## Parser

Tokens become a structured abstract syntax tree according to normative grammar.

## Semantic Analyzer

The analyzer validates names, types, capabilities, references, control flow,
and other language invariants.

## Intermediate Representation

Valid programs compile into an explicit execution graph.

## Runtime

The runtime executes validated graph nodes.

## Capability Adapters

External effects are provided through explicitly enabled capabilities rather
than being implicit language behavior.
