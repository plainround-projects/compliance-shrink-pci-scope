# Regular expressions (the re module)

## What it is

A **regular expression** (regex) is a short pattern that describes a set of strings, like `^## (.+)$` for "a line
that starts with `## `". Python's standard `re` module compiles a pattern into an object you can use to **match** a
string, **search** inside it, **find all** matches or **split** it. Parentheses in a pattern make **groups** whose text
you can read back.

## Why this repository uses it

The documents are Markdown text with simple conventions (`## Heading`, `Label: text`, `Phase 3: name`). The
program recognizes them with a handful of regexes and turns them into typed values. The patterns are compiled once, as
module-level constants with a leading underscore.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/domain/card.py` | `_CANDIDATE`, `_CARD_FIELD`, `_FIELD_NAME_ONLY`: find card numbers and card fields. |
| `src/pci_scope/domain/payment.py` | `TOKEN`: what a payment value must look like. |
| `src/pci_scope/interfaces/browser_sim.py` | Finds the scripts a page loads. |
| `sql/001_schema.sql` | The same idea as `GLOB` patterns in `CHECK` constraints. |

## How it works underneath

`re.compile(pattern)` turns the pattern into a small program for matching. `pattern.match(line)` tries to match from
the **start** of the string and returns a match object or `None`. `pattern.search(text)` looks anywhere. A match
object's `.group(1)` is the text of the first parenthesized part. The symbols used here:

| Symbol | Meaning |
| --- | --- |
| `^` and `$` | start and end of the text |
| `.` | any one character |
| `+`, `*`, `?` | one or more, zero or more, optional |
| `+?`, `.*?` | the same but **lazy**: as few characters as possible |
| `\d`, `\s` | a digit, a whitespace character |
| `[A-Z0-9]` | one character from a set |
| `( ... )` | a group to capture |
| `a|b` | a or b |
| `(?<=x)`, `(?=x)` | look-behind and look-ahead: x must come before or after, but is not part of the match |
| `\.` | a literal dot (a backslash cancels a symbol's meaning) |

A string written `r"..."` is a **raw string**: backslashes are kept as they are, which is what patterns need.

## Walkthrough of this repository's use

`src/pci_scope/domain/card.py`:

```python
# Digits in groups, optionally separated by single spaces or dashes: 13 to 19 digits in all.
_CANDIDATE = re.compile(r"(?<![\d-])(?:\d[ -]?){12,18}\d(?![\d-])")
_CARD_FIELD = re.compile(
    r"""(?i)\b(cvv|cvc|cvv2|card[_\[\]-]*number|card_number|cardnumber|pan)\b["']?\s*[:=]\s*["']?[^\s&,"'}]+"""
)
_FIELD_NAME_ONLY = re.compile(r"(?i)card\[(number|cvc|exp_month|exp_year)\]")
```

- `_CANDIDATE` finds text that **could** be a card number: `(?<![\d-])` is a look-behind meaning "not preceded by a digit or hyphen",
  `(?:\d[ -]?){12,18}` is 12 to 18 repetitions of "a digit, optionally followed by one space or hyphen", then `\d` the last
  digit, and `(?![\d-])` means "not followed by a digit or hyphen". So `4242 4242 4242 4242` and `4242-4242-4242-4242` are candidates;
  a longer run of digits that only contains a card-sized piece is not.
- `_CARD_FIELD` finds the **names** of card fields with a value after them: `(?i)` makes it case-insensitive; `\b(cvv|cvc|cvv2|...)\b`
  matches the name as a whole word; `["']?\s*[:=]\s*["']?[^\s&,"'}]+` is an optional quote, a `:` or `=`, an optional quote and then
  the value (anything but a space, `&`, a comma, a quote or `}`). It catches `cvv=123` in a form body and `"cvc": "123"` in JSON.
- `_FIELD_NAME_ONLY` matches the provider-style names `card[number]`, `card[cvc]`, `card[exp_month]`, `card[exp_year]`.

`src/pci_scope/domain/card.py`:

```python
def scan_text(source: str, text: str) -> list[CardFinding]:
    """Card numbers (13 to 19 digits that pass the Luhn check, spaces or dashes allowed) and card fields with a value.

    The evidence is masked, so the report of a scan never becomes a new copy of the number.
    """
    found: list[CardFinding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in _CANDIDATE.finditer(line):
            digits = re.sub(r"[ -]", "", match.group(0))
            if 13 <= len(digits) <= 19 and luhn_valid(digits):
                found.append(CardFinding(source, line_number, "card number", mask(digits)))
        for field in _CARD_FIELD.finditer(unquote_plus(line)):
            found.append(CardFinding(source, line_number, "card field", field.group(1).lower()))
    return found
```

Each candidate is cleaned (`re.sub(r"[ -]", "", ...)` removes spaces and hyphens), must be 13 to 19 digits and pass the Luhn check
(see `card-number-scanning.md`). `unquote_plus(line)` first decodes `%5B` and `+` so a URL-encoded body is scanned as the text it
really is.

`src/pci_scope/domain/payment.py`:

```python
TOKEN = re.compile(r"^(pi|pm|cus|re)_[A-Za-z0-9]{8,64}$")
```

`TOKEN` accepts a provider id: `(pi|pm|cus|re)` one of four prefixes, `_`, then `[A-Za-z0-9]{8,64}` between 8 and 64 letters or
digits. A card number cannot match, because it has no prefix and no underscore.

`src/pci_scope/interfaces/browser_sim.py`:

```python
    run.scripts = re.findall(r'<script src="([^"]+)"', page.body)
```

`re.findall(r'<script src="([^"]+)"', page.body)` returns the text of every `src="..."` of a script tag in the page: the scripts the
browser would load. `[^"]+` means "one or more characters that are not a double quote".

## Try it yourself

```bash
.venv/bin/python -c "from pci_scope.domain.card import scan_text; print(scan_text('x', 'card 4242 4242 4242 4242 ok'))"
```
Prints one `CardFinding` with `kind='card number'` and `evidence='424242******4242'`: the report masks the number.

```bash
.venv/bin/python -c "from pci_scope.domain.card import scan_text; print(scan_text('x', 'order 1234 5678 9012 3456 ok'))"
```
Prints `[]`: sixteen digits that fail the Luhn check are not a card.

```bash
.venv/bin/python -c "from pci_scope.domain.card import scan_text; print([f.kind for f in scan_text('x', 'cvv=123&card%5Bnumber%5D=4242424242424242')])"
```
Prints `['card number', 'card field']` (order may vary): URL-encoded text is decoded before the fields are searched.

```bash
.venv/bin/python -c "from pci_scope.domain.payment import is_token; print([is_token(v) for v in ('pi_a1ce9a370c7b1637c72cfbd3', 'pm_short', '4242424242424242')])"
```
Prints `[True, False, False]`.

## Mistakes people make

- **Forgetting `r` before the string**, so `\d` is read as a plain `d` with a warning.
- **Greedy matching** that grabs too much: `.+` versus `.+?`.
- **Using `match` when `search` is needed** (`match` only matches at the start).
- **Parsing nested structure with a regex.** Here the patterns recognize single lines, and the code groups lines itself.
- **Not escaping user text** when it is placed inside a pattern. `re.escape` does that (used in the field parser).

## Check yourself

1. Why is `_CANDIDATE` not enough to call something a card?
   **Answer:** It only matches digit groups; the Luhn check must also pass.
2. What does `(?<![\d-])` mean?
   **Answer:** The match must not be preceded by a digit or a hyphen.
3. What does `(?i)` do at the start of `_CARD_FIELD`?
   **Answer:** Makes the whole pattern case-insensitive.
4. Why does `unquote_plus` run before the field search?
   **Answer:** A URL-encoded body hides `card[number]` as `card%5Bnumber%5D`.
5. Why can a card number never match `TOKEN`?
   **Answer:** A token needs a prefix such as `pi_` or `pm_`, which a number does not have.

## Further reading

- `re` (Python 3.12): <https://docs.python.org/3.12/library/re.html>
- Regular Expression HOWTO: <https://docs.python.org/3.12/howto/regex.html>
