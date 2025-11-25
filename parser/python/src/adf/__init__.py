"""
ADF (Augmentable Data Format) Parser

A Python reference implementation of the ADF specification.
"""

from .parser import parse, parse_file
from .document import Document
from .errors import ADFError, ADFParseError, ADFValidationError
from . import serializer  # noqa: F401 - Import to activate Document.serialize()

__version__ = "0.1.0"
__all__ = [
    "parse",
    "parse_file",
    "Document",
    "ADFError",
    "ADFParseError",
    "ADFValidationError",
]
