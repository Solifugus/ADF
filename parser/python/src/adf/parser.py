"""
Main ADF parser
"""

from pathlib import Path
from typing import Any, Optional
from .lexer import Lexer, Token, LineType
from .document import Document
from .errors import ADFParseError


class Parser:
    """
    Parser for ADF format.

    Converts tokenized ADF into a Document structure.
    """

    def __init__(self, strict: bool = False, infer_types: bool = True):
        """
        Initialize parser.

        Args:
            strict: If True, raise errors on malformed input.
                   If False, skip malformed lines with warnings.
            infer_types: If True, infer types (int, float, bool) from string values.
                        If False, keep all values as strings.
        """
        self.strict = strict
        self.infer_types = infer_types

    def parse(self, text: str) -> Document:
        """
        Parse ADF text into a Document.

        Args:
            text: ADF text to parse

        Returns:
            Parsed Document

        Raises:
            ADFParseError: If parsing fails in strict mode
        """
        lexer = Lexer(text, strict=self.strict)
        tokens = lexer.tokenize()

        document = Document()
        self._parse_tokens(tokens, document)

        return document

    def _parse_tokens(self, tokens: list[Token], document: Document) -> None:
        """Parse tokens into document structure"""
        i = 0
        current_section_path = ""
        current_is_absolute = True
        section_start = 0

        while i < len(tokens):
            token = tokens[i]

            if token.line_type in (LineType.ABSOLUTE_HEADER, LineType.RELATIVE_HEADER):
                # Process previous section if any
                if i > section_start:
                    section_tokens = tokens[section_start:i]
                    self._process_section(
                        section_tokens,
                        current_section_path,
                        current_is_absolute,
                        document,
                    )

                # Start new section
                current_section_path = token.path or ""
                current_is_absolute = token.is_absolute or False
                section_start = i + 1

            i += 1

        # Process final section
        if section_start < len(tokens):
            section_tokens = tokens[section_start:]
            self._process_section(
                section_tokens,
                current_section_path,
                current_is_absolute,
                document,
            )

    def _process_section(
        self,
        tokens: list[Token],
        section_path: str,
        is_absolute: bool,
        document: Document,
    ) -> None:
        """Process a section's tokens"""
        if not tokens:
            return

        # Filter out blank lines for analysis
        content_tokens = [t for t in tokens if t.line_type != LineType.BLANK]
        if not content_tokens:
            return

        # Determine section type
        has_key_value = any(
            t.line_type in (LineType.KEY_VALUE, LineType.MULTILINE_START)
            for t in content_tokens
        )

        if not has_key_value:
            # Scalar array
            values = [self._infer_type(t.value) for t in content_tokens if t.value is not None]
            if is_absolute:
                document.set(section_path, values)
            else:
                document.add_relative_section(section_path, values)
        else:
            # Check for object array (has blank line separators)
            if self._has_blank_line_separators(tokens):
                # Object array
                objects = self._parse_object_array(tokens)
                if is_absolute:
                    document.set(section_path, objects)
                else:
                    document.add_relative_section(section_path, objects)
            else:
                # Plain object
                obj = self._parse_object(tokens)
                if is_absolute:
                    for key, value in obj.items():
                        full_path = f"{section_path}.{key}" if section_path else key
                        document.merge_at_path(full_path, value)
                else:
                    document.add_relative_section(section_path, obj)

    def _has_blank_line_separators(self, tokens: list[Token]) -> bool:
        """Check if tokens have blank lines separating key-value blocks"""
        has_blank = False
        has_content_after_blank = False

        found_content = False
        for token in tokens:
            if token.line_type == LineType.BLANK:
                if found_content:
                    has_blank = True
                    found_content = False
            elif token.line_type in (LineType.KEY_VALUE, LineType.MULTILINE_START):
                if has_blank:
                    has_content_after_blank = True
                found_content = True

        return has_blank and has_content_after_blank

    def _parse_object_array(self, tokens: list[Token]) -> list[dict[str, Any]]:
        """Parse tokens as an array of objects"""
        objects = []
        current_object: dict[str, Any] = {}

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token.line_type == LineType.BLANK:
                if current_object:
                    objects.append(current_object)
                    current_object = {}
            elif token.line_type == LineType.KEY_VALUE:
                key, value = token.key, token.value
                if key:
                    current_object[key] = self._infer_type(value)
            elif token.line_type == LineType.MULTILINE_START:
                # Collect multiline value
                value, i = self._collect_multiline(tokens, i)
                if token.key:
                    current_object[token.key] = value

            i += 1

        # Don't forget last object
        if current_object:
            objects.append(current_object)

        return objects

    def _parse_object(self, tokens: list[Token]) -> dict[str, Any]:
        """Parse tokens as a plain object"""
        obj: dict[str, Any] = {}

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token.line_type == LineType.KEY_VALUE:
                key, value = token.key, token.value
                if key:
                    self._set_nested_value(obj, key, self._infer_type(value))
            elif token.line_type == LineType.MULTILINE_START:
                # Collect multiline value
                value, i = self._collect_multiline(tokens, i)
                if token.key:
                    self._set_nested_value(obj, token.key, value)

            i += 1

        return obj

    def _collect_multiline(self, tokens: list[Token], start_idx: int) -> tuple[str, int]:
        """
        Collect a multiline value starting from a MULTILINE_START token.

        Returns:
            (value, last_index)
        """
        parts = []

        # Add initial content from start token
        if tokens[start_idx].value:
            parts.append(tokens[start_idx].value)

        i = start_idx + 1
        while i < len(tokens):
            token = tokens[i]

            if token.line_type == LineType.MULTILINE_CONTENT:
                parts.append(token.value or "")
            elif token.line_type == LineType.MULTILINE_END:
                if token.value:
                    parts.append(token.value)
                break

            i += 1

        value = "\n".join(parts)
        return value, i

    def _set_nested_value(self, obj: dict[str, Any], key: str, value: Any) -> None:
        """
        Set a value in obj using a potentially nested key.

        Examples:
            "name" -> obj["name"] = value
            "address.city" -> obj["address"]["city"] = value
        """
        if "." in key:
            parts = key.split(".")
            current = obj

            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                elif not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]

            current[parts[-1]] = value
        else:
            obj[key] = value

    def _infer_type(self, value: Optional[str]) -> Any:
        """
        Infer type from string value if type inference is enabled.

        Args:
            value: String value to infer type from

        Returns:
            Typed value (int, float, bool, or str)
        """
        if value is None:
            return None

        if not self.infer_types:
            return value

        # Try boolean
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False

        # Try integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Keep as string
        return value


def parse(text: str, mode: str = "lenient", infer_types: bool = True) -> Document:
    """
    Parse ADF text into a Document.

    Args:
        text: ADF text to parse
        mode: "strict" or "lenient" parsing mode
        infer_types: Whether to infer types (int, float, bool) from strings

    Returns:
        Parsed Document

    Raises:
        ADFParseError: If parsing fails in strict mode
    """
    strict = mode == "strict"
    parser = Parser(strict=strict, infer_types=infer_types)
    return parser.parse(text)


def parse_file(path: str, mode: str = "lenient", infer_types: bool = True) -> Document:
    """
    Parse an ADF file into a Document.

    Args:
        path: Path to ADF file
        mode: "strict" or "lenient" parsing mode
        infer_types: Whether to infer types from strings

    Returns:
        Parsed Document

    Raises:
        ADFParseError: If parsing fails in strict mode
        FileNotFoundError: If file doesn't exist
    """
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    return parse(text, mode=mode, infer_types=infer_types)
