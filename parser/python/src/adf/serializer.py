"""
Serializer for converting Document back to ADF format
"""

from typing import Any
from .document import Document


class Serializer:
    """Serializes a Document to ADF format"""

    def __init__(self, indent: str = ""):
        """
        Initialize serializer.

        Args:
            indent: Indentation to use (empty string for none)
        """
        self.indent = indent

    def serialize(self, document: Document) -> str:
        """
        Serialize a Document to ADF text.

        Args:
            document: Document to serialize

        Returns:
            ADF-formatted text
        """
        lines = []
        root_data = document.to_dict()

        # Serialize absolute sections
        self._serialize_dict(root_data, "", lines, is_absolute=True)

        # Serialize relative sections
        relative = document.get_relative_sections()
        if relative:
            if lines:
                lines.append("")  # Blank line before relative sections
            self._serialize_dict(relative, "", lines, is_absolute=False)

        return "\n".join(lines)

    def _serialize_dict(
        self,
        data: dict[str, Any],
        parent_path: str,
        lines: list[str],
        is_absolute: bool,
    ) -> None:
        """
        Recursively serialize a dictionary.

        Args:
            data: Dictionary to serialize
            parent_path: Parent path for this data
            lines: List to append output lines to
            is_absolute: Whether this is an absolute or relative section
        """
        for key, value in data.items():
            current_path = f"{parent_path}.{key}" if parent_path else key

            if isinstance(value, dict):
                # Check if it's a simple object or nested structure
                if self._is_simple_object(value):
                    # Write as section with key-value pairs
                    self._write_section_header(current_path, lines, is_absolute)
                    self._write_object(value, lines)
                    lines.append("")  # Blank line after section
                else:
                    # Recursively handle nested structure
                    self._serialize_dict(value, current_path, lines, is_absolute)

            elif isinstance(value, list):
                # Write array section
                self._write_section_header(current_path, lines, is_absolute)
                self._write_array(value, lines)
                lines.append("")  # Blank line after section

            else:
                # Scalar value at top level - write as section with value
                self._write_section_header(current_path, lines, is_absolute)
                self._write_value(key, value, lines)
                lines.append("")

    def _is_simple_object(self, obj: dict[str, Any]) -> bool:
        """Check if an object is simple (no nested dicts or arrays)"""
        for value in obj.values():
            if isinstance(value, (dict, list)):
                return False
        return True

    def _write_section_header(self, path: str, lines: list[str], is_absolute: bool) -> None:
        """Write a section header"""
        prefix = "# " if is_absolute else ""
        if path:
            lines.append(f"{prefix}{path}:")
        else:
            lines.append(f"{prefix}:")

    def _write_object(self, obj: dict[str, Any], lines: list[str]) -> None:
        """Write an object's key-value pairs"""
        for key, value in obj.items():
            self._write_value(key, value, lines)

    def _write_array(self, arr: list[Any], lines: list[str]) -> None:
        """Write an array"""
        if not arr:
            return

        # Check if it's a scalar array or object array
        if all(not isinstance(item, dict) for item in arr):
            # Scalar array
            for item in arr:
                lines.append(str(item))
        else:
            # Object array
            for i, item in enumerate(arr):
                if i > 0:
                    lines.append("")  # Blank line between objects
                if isinstance(item, dict):
                    self._write_object(item, lines)
                else:
                    lines.append(str(item))

    def _write_value(self, key: str, value: Any, lines: list[str]) -> None:
        """Write a key-value pair"""
        if isinstance(value, str) and "\n" in value:
            # Multiline value
            lines.append(f'{key} = """')
            lines.append(value)
            lines.append('"""')
        else:
            # Simple value
            value_str = self._format_value(value)
            lines.append(f"{key} = {value_str}")

    def _format_value(self, value: Any) -> str:
        """Format a value for output"""
        if isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, str):
            # Check if string needs quoting
            if self._needs_quoting(value):
                return f'"{value}"'
            return value
        else:
            return str(value)

    def _needs_quoting(self, s: str) -> bool:
        """Check if a string needs to be quoted"""
        # Quote if contains special characters or looks like a number/boolean
        if not s:
            return True

        # Check if looks like a type we'd infer
        if s.lower() in ("true", "false"):
            return True

        try:
            float(s)
            return True
        except ValueError:
            pass

        # Check for special characters that might need quoting
        special_chars = ["=", "#", ":", "(", ")"]
        if any(char in s for char in special_chars):
            return True

        return False


# Add serialize method to Document
def _document_serialize(self: Document) -> str:
    """Serialize this document to ADF format"""
    serializer = Serializer()
    return serializer.serialize(self)


# Monkey patch the Document class
Document.serialize = _document_serialize  # type: ignore
