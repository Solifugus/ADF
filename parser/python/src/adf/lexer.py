"""
Lexer for ADF format - handles line-level tokenization
"""

import re
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class LineType(Enum):
    """Types of lines in ADF"""

    BLANK = "blank"
    ABSOLUTE_HEADER = "absolute_header"
    RELATIVE_HEADER = "relative_header"
    KEY_VALUE = "key_value"
    SCALAR_VALUE = "scalar_value"
    MULTILINE_START = "multiline_start"
    MULTILINE_CONTENT = "multiline_content"
    MULTILINE_END = "multiline_end"


@dataclass
class Token:
    """Represents a parsed line"""

    line_type: LineType
    line_number: int
    raw_line: str

    # For headers
    path: Optional[str] = None
    is_absolute: Optional[bool] = None

    # For key-value pairs
    key: Optional[str] = None
    value: Optional[str] = None
    constraint: Optional[str] = None

    # For multiline tracking
    quote_count: Optional[int] = None


class Lexer:
    """Tokenizes ADF text line by line"""

    # Pattern for valid path/key components
    KEY_PATTERN = re.compile(r'^[A-Za-z0-9_]+$')

    # Pattern for quoted keys (simplified - handles basic quoted keys)
    QUOTED_KEY_PATTERN = re.compile(r'^"([^"]+)"$')

    def __init__(self, text: str, strict: bool = False):
        self.lines = text.splitlines()
        self.strict = strict
        self.in_multiline = False
        self.multiline_quote_count = 0

    def tokenize(self) -> list[Token]:
        """Tokenize all lines"""
        tokens = []
        for i, line in enumerate(self.lines, start=1):
            token = self._tokenize_line(line, i)
            if token:
                tokens.append(token)
        return tokens

    def _tokenize_line(self, line: str, line_number: int) -> Optional[Token]:
        """Tokenize a single line"""

        # Handle multiline continuation
        if self.in_multiline:
            return self._handle_multiline_continuation(line, line_number)

        # Check for blank line
        if not line.strip():
            return Token(
                line_type=LineType.BLANK,
                line_number=line_number,
                raw_line=line,
            )

        # Check for header (absolute or relative)
        header_token = self._try_parse_header(line, line_number)
        if header_token:
            return header_token

        # Check for key-value pair
        if "=" in line:
            return self._parse_key_value(line, line_number)

        # Otherwise, it's a scalar value
        return Token(
            line_type=LineType.SCALAR_VALUE,
            line_number=line_number,
            raw_line=line,
            value=line.strip(),
        )

    def _try_parse_header(self, line: str, line_number: int) -> Optional[Token]:
        """Try to parse line as a header"""
        stripped = line.strip()

        if not stripped.endswith(":"):
            return None

        # Remove trailing colon
        path_part = stripped[:-1].strip()

        # Check if absolute (starts with #)
        is_absolute = False
        if path_part.startswith("#"):
            is_absolute = True
            path_part = path_part[1:].strip()

        # Special case: root section (#:)
        if not path_part:
            if is_absolute:
                return Token(
                    line_type=LineType.ABSOLUTE_HEADER,
                    line_number=line_number,
                    raw_line=line,
                    path="",
                    is_absolute=True,
                )
            else:
                # Relative section with no path - probably an error
                return None

        # Validate path
        if not self._is_valid_path(path_part):
            return None

        return Token(
            line_type=LineType.ABSOLUTE_HEADER if is_absolute else LineType.RELATIVE_HEADER,
            line_number=line_number,
            raw_line=line,
            path=path_part,
            is_absolute=is_absolute,
        )

    def _parse_key_value(self, line: str, line_number: int) -> Token:
        """Parse a key=value line"""
        # Find first = that's not in a quote block
        equals_pos = line.find("=")
        if equals_pos == -1:
            # Should not happen, but handle gracefully
            return Token(
                line_type=LineType.SCALAR_VALUE,
                line_number=line_number,
                raw_line=line,
                value=line.strip(),
            )

        raw_key = line[:equals_pos].strip()
        raw_value = line[equals_pos + 1 :].lstrip()

        # Parse key (may include dots for nested paths)
        key = self._parse_key(raw_key)

        # Check if value starts a multiline block
        quote_count = self._count_leading_quotes(raw_value)
        if quote_count > 0:
            # Starting a multiline value
            self.in_multiline = True
            self.multiline_quote_count = quote_count

            # Check if it also ends on the same line (single-line quoted value)
            # Need at least quote_count*2 chars and must end with those quotes
            if (
                len(raw_value) > quote_count * 2
                and self._ends_with_quotes(raw_value, quote_count)
            ):
                # Single-line quoted value
                self.in_multiline = False
                value = self._extract_quoted_value(raw_value, quote_count)
                constraint = self._extract_constraint(raw_value, quote_count)
                return Token(
                    line_type=LineType.KEY_VALUE,
                    line_number=line_number,
                    raw_line=line,
                    key=key,
                    value=value,
                    constraint=constraint,
                )
            else:
                # Multiline start
                content = raw_value[quote_count:]
                return Token(
                    line_type=LineType.MULTILINE_START,
                    line_number=line_number,
                    raw_line=line,
                    key=key,
                    value=content,
                    quote_count=quote_count,
                )

        # Simple value (possibly with constraint)
        value, constraint = self._parse_value_and_constraint(raw_value)

        return Token(
            line_type=LineType.KEY_VALUE,
            line_number=line_number,
            raw_line=line,
            key=key,
            value=value,
            constraint=constraint,
        )

    def _handle_multiline_continuation(self, line: str, line_number: int) -> Token:
        """Handle a line within a multiline block"""
        # Check if this line ends the multiline block
        if self._ends_with_quotes(line, self.multiline_quote_count):
            self.in_multiline = False
            # Remove trailing quotes and extract any constraint
            content = line[: -self.multiline_quote_count].rstrip()
            # Look for constraint after the quotes
            constraint = self._extract_constraint_after_line(line, self.multiline_quote_count)
            return Token(
                line_type=LineType.MULTILINE_END,
                line_number=line_number,
                raw_line=line,
                value=content,
                constraint=constraint,
            )
        else:
            # Content line
            return Token(
                line_type=LineType.MULTILINE_CONTENT,
                line_number=line_number,
                raw_line=line,
                value=line,
            )

    def _is_valid_path(self, path: str) -> bool:
        """Check if a path is valid"""
        if not path:
            return True  # Empty path is valid for root

        parts = path.split(".")
        for part in parts:
            # Check for quoted key
            quoted_match = self.QUOTED_KEY_PATTERN.match(part)
            if quoted_match:
                continue  # Quoted keys are valid

            # Check regular key pattern
            if not self.KEY_PATTERN.match(part):
                return False
        return True

    def _parse_key(self, key: str) -> str:
        """Parse and validate a key"""
        # Keys can contain dots for nested paths
        # Keys can be quoted
        return key

    def _count_leading_quotes(self, s: str) -> int:
        """Count consecutive quotes at the start of string"""
        count = 0
        for char in s:
            if char == '"':
                count += 1
            else:
                break
        return count

    def _ends_with_quotes(self, s: str, count: int) -> bool:
        """Check if string ends with exactly 'count' quotes"""
        if len(s) < count:
            return False
        return s[-count:] == '"' * count

    def _extract_quoted_value(self, s: str, quote_count: int) -> str:
        """Extract value from within quotes"""
        if len(s) < quote_count * 2:
            return ""
        return s[quote_count:-quote_count]

    def _extract_constraint(self, s: str, quote_count: int) -> Optional[str]:
        """Extract constraint from after quoted value"""
        # Find the closing quotes
        if len(s) < quote_count * 2:
            return None

        after_quotes = s[len(s) - quote_count :].lstrip()
        return self._parse_constraint(after_quotes)

    def _extract_constraint_after_line(self, line: str, quote_count: int) -> Optional[str]:
        """Extract constraint after closing quotes on a line"""
        if len(line) < quote_count:
            return None

        after_quotes = line[len(line) - quote_count :].strip()
        if after_quotes.startswith('"'):
            # Remove the quotes
            after_quotes = after_quotes[quote_count:].lstrip()

        return self._parse_constraint(after_quotes)

    def _parse_value_and_constraint(self, s: str) -> Tuple[str, Optional[str]]:
        """Parse a value and optional constraint"""
        # Look for constraint in parentheses
        # Simple approach: find last (...)
        constraint = self._parse_constraint(s)
        if constraint:
            # Remove constraint from value
            paren_pos = s.rfind("(")
            value = s[:paren_pos].rstrip()
        else:
            value = s.strip()

        return value, constraint

    def _parse_constraint(self, s: str) -> Optional[str]:
        """Extract constraint from string"""
        s = s.strip()
        if not s:
            return None

        # Find last opening parenthesis
        open_paren = s.rfind("(")
        if open_paren == -1:
            return None

        # Find matching closing parenthesis
        close_paren = s.rfind(")")
        if close_paren == -1 or close_paren < open_paren:
            return None

        # Extract constraint content
        constraint = s[open_paren + 1 : close_paren].strip()
        return constraint if constraint else None
