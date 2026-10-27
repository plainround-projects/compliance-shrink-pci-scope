# Card numbers, the Luhn check and the scanner

## What it is

A **card number** (PAN, primary account number) is 13 to 19 digits. The last digit is a **check digit** computed by the **Luhn
algorithm**, so a mistyped number is usually caught: starting from the right, double every second digit (subtracting 9 if the result is
over 9), add everything up, and the total must end in 0. The test cards used here (`4242 4242 4242 4242`) are published by payment
providers and are not real accounts. A **scanner** searches text for things that look like card data. To keep the report from becoming a
new copy of the number, results are **masked**: first six and last four digits, stars between.

## Why this repository uses it

"No card data on our side" is a claim that must be checked, not asserted. The scanner reads the merchant's log, the database (as SQL
text) and the backups, and reports any Luhn-valid number or card field. It also scans the HAR capture and the evidence folder itself.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/domain/card.py` | `luhn_valid`, `mask`, `scan_text`, `card_field_names`, the test cards. |
| `src/pci_scope/application/proof.py` | `run_scan` runs the scanner over a set of artifacts. |
| `src/pci_scope/infrastructure/artifacts.py` | What gets scanned (see `pathlib.md`). |
| `pci-scope scan PATH...` | The command line entry. |
| `evidence/proof-before.txt`, `proof-after.txt` | The scan of the naive and the redesigned merchant. |

## How it works underneath

The scanner works in two passes per line. First a regular expression finds digit groups that could be a card number (see `re.md`).
Then the Luhn check removes lookalikes such as order numbers. A line is also searched for **card field names with values**
(`cvv=123`, `"cvc": "123"`), because a CVV alone is also forbidden to store. Because a form body may be URL-encoded, the line is decoded
before the field search.

## Walkthrough of this repository's use

`src/pci_scope/domain/card.py`:

```python
def luhn_valid(digits: str) -> bool:
    """The Luhn check every card number passes."""
    if not digits.isdigit():
        return False
    total = 0
    for position, char in enumerate(reversed(digits)):
        value = int(char)
        if position % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0
```

- `digits.isdigit()` rejects anything that is not only digits.
- `reversed(digits)` walks from the right; `enumerate(..., )` gives a position. Every second digit (odd positions) is doubled, and `value
  -= 9` when it is over 9 (the same as adding its two digits). The total modulo 10 must be 0.

`src/pci_scope/domain/card.py`:

```python
def mask(digits: str) -> str:
    """The first six and last four digits, the rest as stars: enough to tell the card in a report, never the number."""
    return f"{digits[:6]}{'*' * (len(digits) - 10)}{digits[-4:]}"
```

`digits[:6]` the first six, `'*' * (len(digits) - 10)` stars for the middle, `digits[-4:]` the last four. `4242424242424242` becomes
`424242******4242`: enough to tell which card in a report, never enough to use it.

`src/pci_scope/domain/card.py`:

```python
TEST_CARD = "4242424242424242"
DECLINED_TEST_CARD = "4000000000000002"
TEST_CARDS = frozenset({TEST_CARD, DECLINED_TEST_CARD})
```

The two published test cards: one that succeeds and one that the provider stand-in declines.

`src/pci_scope/domain/card.py`:

```python
@dataclass(frozen=True)
class CardFinding:
    """Card data found in a place where it must not be."""

    source: str
    line: int
    kind: str
    evidence: str
```

A finding records the source, the line, the kind (`card number` or `card field`) and the **masked** evidence.

## Try it yourself

```bash
.venv/bin/python -c "from pci_scope.domain.card import luhn_valid, mask; print(luhn_valid('4242424242424242'), luhn_valid('4242424242424241'), mask('4242424242424242'))"
```
Prints `True False 424242******4242`.

```bash
printf 'paid with 4242 4242 4242 4242\n' > /tmp/leaky.log && make scan PATHS=/tmp/leaky.log; echo "exit: $?"
```
Prints `/tmp/leaky.log:1 FOUND card number 424242******4242` (masked), then Make reports `Error 1` and the shell shows `exit: 2` (Make's
code for a failed recipe; the scanner itself exited 1). Going through `make` loads the settings from `.env`.

```bash
make scan PATHS="evidence"
```
Scans the evidence folder; finds nothing (masked evidence only).

```bash
cat evidence/proof-before.txt | head -6
```
Shows the scan of the naive checkout: findings with masked numbers.

## Mistakes people make

- **Printing the number you found.** The report masks it.
- **Treating every 16-digit number as a card.** The Luhn check separates cards from order numbers.
- **Storing a CVV "just for a moment".** It is forbidden after authorization; the scanner looks for field names too.
- **Scanning only text files.** The scanner decodes binary files leniently so it misses nothing.
- **Using a real card to test.** Only the published test cards.

## Check yourself

1. What does the Luhn check detect?
   **Answer:** Most single mistyped digits and many swaps, using the check digit.
2. Why mask the evidence?
   **Answer:** So the report does not become another copy of the card number.
3. Why also search for field names like `cvv`?
   **Answer:** A CVV may be stored without a card number next to it, and is forbidden too.
4. Why decode URL-encoded text before searching?
   **Answer:** `card%5Bnumber%5D` hides the field name.
5. What are `4242424242424242` and `4000000000000002`?
   **Answer:** Published test cards: one succeeds, one is declined.

## Further reading

- Luhn algorithm (ISO/IEC 7812-1): <https://www.iso.org/standard/70484.html>
- PCI Security Standards Council, documents library: <https://www.pcisecuritystandards.org/document_library/>
- Test card numbers are published in each payment provider's own documentation.
