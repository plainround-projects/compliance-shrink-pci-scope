# 3. Scope is computed from an inventory

Status: accepted, 2026-10-27

## Context

The lesson asks for the cardholder data environment before and after, with the systems that are in scope and why. Diagrams drawn by hand disagree with the list after the first change.

## Decision

Describe the systems and their connections in `scope/*.toml`: which systems card data reaches directly, which serves the payment page, and which connections carry card data (`data`) or can change a system (`control`). `compute_scope` spreads card data along `data` edges, adds the page host, then adds every system that can change an in-scope one, directly or through others, and collects the teams. The Mermaid diagrams and the reports are generated from the same result, and tests pin the lesson's numbers (9 systems and 3 teams before).

## Alternatives considered

- **Draw it by hand in a diagram tool.** Nothing checks it against the list.
- **A rule per system.** Longer and still not tied to how the data moves.

## Consequences

- Changing the inventory changes every document; the verification fails if a document says otherwise.
- The inventory describes a typical setup; a real assessment starts from the real network.
