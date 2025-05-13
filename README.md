# Compiler Project - Scanner & Parser

## Files
- `scanner.py`: Tokenizes the custom Project #3 language
- `parser.py`: Parses token sequences using simplified grammar
- Tested with sample code from the specification

## Usage
You can import both modules and use `run_scanner(filepath)` to get tokens and `Parser(tokens).parse()` to get syntax validation.

## Example
```python
from scanner import run_scanner
from pars import Parser

tokens, errors = run_scanner("your_code.txt")
parser = Parser(tokens)
results = parser.parse()

for line in results:
    print(line)
```
