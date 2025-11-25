# ADF Python Parser

Reference implementation of the Augmentable Data Format (ADF) parser in Python.

## Installation

```bash
pip install adf-parser
```

Or install from source:

```bash
cd parser/python
pip install -e .
```

## Quick Start

```python
from adf import parse, parse_file

# Parse from string
text = """
# person:
name = Matthew
age = 54

# person.hobbies:
reading
physics
coding
"""

doc = parse(text)
print(doc.get('person.name'))  # "Matthew"
print(doc.get('person.hobbies'))  # ["reading", "physics", "coding"]

# Parse from file
doc = parse_file('config.adf')

# Access nested data
value = doc.get('server.port')

# Export to dict/JSON
data = doc.to_dict()
json_data = doc.to_json()

# Serialize back to ADF
adf_text = doc.serialize()
```

## Features

- ✅ Full ADF specification compliance
- ✅ Absolute and relative sections
- ✅ Scalar and object arrays
- ✅ Multiline values with quote delimiters
- ✅ Constraint annotations
- ✅ Document merging and augmentation
- ✅ Type inference (optional)
- ✅ Strict and lenient parsing modes
- ✅ Round-trip serialization

## API

### Parsing

```python
parse(text: str, mode: str = 'lenient', infer_types: bool = True) -> Document
parse_file(path: str, mode: str = 'lenient', infer_types: bool = True) -> Document
```

### Document

```python
doc.get(path: str, default: Any = None) -> Any
doc.set(path: str, value: Any) -> None
doc.merge(other: Document) -> None
doc.to_dict() -> dict
doc.to_json() -> str
doc.serialize() -> str
```

## Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=adf --cov-report=html
```

## License

MIT License - See LICENSE file for details
