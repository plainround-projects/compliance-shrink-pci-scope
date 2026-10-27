# Mermaid diagrams

## What it is

Mermaid is a text language for diagrams. You write `flowchart LR` and lines like `a["Web server"] --> b["Log"]`, and a viewer (GitHub,
many editors) draws boxes and arrows. The diagram lives in a Markdown file inside a fenced block marked `mermaid`.

## Why this repository uses it

The lesson asks for a diagram showing where card data goes. Because the diagram is generated from the inventory, it cannot disagree with
the numbers next to it, and a change in the inventory changes the picture.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/domain/scope.py` | `render_mermaid` and `render_scope_report`. |
| `evidence/scope-before.md`, `scope-after.md` | The generated diagrams and tables. |
| `README.md`, `ARCHITECTURE.md` | May embed the same diagrams. |

## How it works underneath

A viewer reads the text and lays out the graph. `flowchart LR` means left to right. `subgraph cde["In scope"] ... end` draws a box
around a group. `a --> b` is a solid arrow, `a -.-> b` a dotted one, and `|label|` labels it. Nothing runs: it is only text.

## Walkthrough of this repository's use

`src/pci_scope/domain/scope.py`:

```python
def render_mermaid(inventory: Inventory, result: ScopeResult) -> str:
    """The cardholder data environment as a Mermaid flowchart: in-scope systems inside a subgraph, the rest outside."""
    lines = ["flowchart LR"]
    inside = [system for system in inventory.systems if system.id in result.ids]
    outside = [system for system in inventory.systems if system.id not in result.ids]
    lines.append('    subgraph cde["In scope"]')
    lines += [f'        {system.id}["{system.name}"]' for system in inside] or ['        none["nothing"]']
    lines.append("    end")
    lines += [f'    {system.id}["{system.name}{" (provider)" if system.external else ""}"]' for system in outside]
    for edge in inventory.edges:
        arrow = "-->" if edge.kind == DATA else "-.->"
        label = "card data" if edge.kind == DATA else "can change"
        lines.append(f"    {edge.source} {arrow}|{label}| {edge.target}")
    return "\n".join(lines)
```

- The first line is `flowchart LR`.
- A `subgraph cde["In scope"]` box holds the in-scope systems; the rest are drawn outside it (an external provider is labeled `(provider)`).
- Each edge becomes a line. A `data` edge is a solid arrow labeled `card data`; a `control` edge is a dotted arrow labeled `can change`.
- The result is a list of strings joined with newlines.

`evidence/scope-after.md`:

````markdown
# After: the card number goes from the browser to the provider

```mermaid
flowchart LR
    subgraph cde["In scope"]
        web["Web server (serves the checkout page)"]
        ci["CI/CD pipeline"]
        admin["Admin accounts"]
    end
    browser["Customer browser (provider)"]
    provider["Payment provider (hosted fields) (provider)"]
    log["Request log"]
    shipping["Log shipping"]
    search["Log search tool"]
````

The generated report: the diagram in a fenced block, then a one-line count, then a table of in-scope systems with the reason for each.

## Try it yourself

```bash
head -16 evidence/scope-before.md
```
Shows the generated diagram text and the start of the table.

```bash
make scope | head -14
```
Prints the same report for the naive checkout (needs no server).

```bash
grep -c -- "-->" evidence/scope-before.md evidence/scope-after.md
```
Counts the solid (card-data) arrows in each diagram.

```bash
grep -n "subgraph" evidence/scope-after.md
```
Shows the box that marks what is in scope.

## Mistakes people make

- **Drawing the diagram by hand**, where it can drift from the facts. Here it is generated.
- **Ids with spaces** in Mermaid; the code uses short ids and puts the display text in quotes.
- **Assuming every Markdown viewer draws it.** GitHub does; a plain text editor shows the source.

## Check yourself

1. What does `flowchart LR` mean?
   **Answer:** A flowchart laid out left to right.
2. What is the difference between `-->` and `-.->`?
   **Answer:** Solid for card data, dotted for "can change".
3. What does a `subgraph` do?
   **Answer:** Draws a box around a group of nodes.
4. Why is the diagram generated?
   **Answer:** So it always agrees with the inventory.
5. Is Mermaid executed?
   **Answer:** No; it is text that a viewer draws.

## Further reading

- Mermaid documentation: <https://mermaid.js.org/intro/>
- Flowcharts: <https://mermaid.js.org/syntax/flowchart.html>
