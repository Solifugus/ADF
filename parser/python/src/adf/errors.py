"""
Error definitions for ADF parser
"""

from typing import Optional


class ADFError(Exception):
    """Base exception for all ADF errors"""

    pass


class ADFParseError(ADFError):
    """Raised when parsing fails"""

    def __init__(
        self,
        message: str,
        line_number: Optional[int] = None,
        line: Optional[str] = None,
    ):
        self.message = message
        self.line_number = line_number
        self.line = line

        full_message = message
        if line_number is not None:
            full_message = f"Line {line_number}: {message}"
        if line is not None:
            full_message += f"\n  {line}"

        super().__init__(full_message)


class ADFValidationError(ADFError):
    """Raised when validation fails"""

    def __init__(self, message: str, path: Optional[str] = None):
        self.message = message
        self.path = path

        full_message = message
        if path:
            full_message = f"At '{path}': {message}"

        super().__init__(full_message)
