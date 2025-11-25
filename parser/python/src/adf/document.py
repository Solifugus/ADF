"""
Document data model for ADF
"""

import json
from typing import Any, Optional, Union


class Document:
    """
    Represents a parsed ADF document.

    Provides access to the hierarchical data structure
    and methods for manipulation and serialization.
    """

    def __init__(self) -> None:
        self._root: dict[str, Any] = {}
        self._relative_sections: dict[str, Any] = {}

    def get(self, path: str, default: Any = None) -> Any:
        """
        Get a value by dot-notation path.

        Args:
            path: Dot-separated path (e.g., "person.name")
            default: Default value if path not found

        Returns:
            The value at the path, or default if not found
        """
        if not path:
            return self._root

        parts = self._parse_path(path)
        current = self._root

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default

        return current

    def set(self, path: str, value: Any) -> None:
        """
        Set a value by dot-notation path.

        Args:
            path: Dot-separated path (e.g., "person.name")
            value: Value to set
        """
        if not path:
            if isinstance(value, dict):
                self._root = value
            return

        parts = self._parse_path(path)
        current = self._root

        # Navigate to parent, creating dicts as needed
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                # Overwrite non-dict with dict
                current[part] = {}
            current = current[part]

        # Set the final value
        current[parts[-1]] = value

    def merge(self, other: "Document") -> None:
        """
        Merge another document into this one.

        Later values override earlier ones for scalars.
        Objects are merged recursively.
        Arrays are replaced (not appended).

        Args:
            other: Document to merge from
        """
        self._root = self._deep_merge(self._root, other._root)

    def merge_at_path(self, path: str, data: Any) -> None:
        """
        Merge data at a specific path.

        Args:
            path: Where to merge the data
            data: Data to merge
        """
        existing = self.get(path, {})
        if isinstance(existing, dict) and isinstance(data, dict):
            merged = self._deep_merge(existing, data)
            self.set(path, merged)
        else:
            self.set(path, data)

    def to_dict(self) -> dict[str, Any]:
        """Convert document to a dictionary"""
        return self._deep_copy(self._root)

    def to_json(self, indent: Optional[int] = 2) -> str:
        """
        Convert document to JSON string.

        Args:
            indent: Indentation level (None for compact)

        Returns:
            JSON string
        """
        return json.dumps(self._root, indent=indent)

    def get_relative_sections(self) -> dict[str, Any]:
        """Get all relative sections (relocatable fragments)"""
        return self._deep_copy(self._relative_sections)

    def add_relative_section(self, path: str, data: Any) -> None:
        """
        Add a relative section.

        Args:
            path: Path of the relative section
            data: Data for the section
        """
        parts = self._parse_path(path)
        current = self._relative_sections

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        if parts[-1] in current and isinstance(current[parts[-1]], dict) and isinstance(data, dict):
            current[parts[-1]] = self._deep_merge(current[parts[-1]], data)
        else:
            current[parts[-1]] = data

    def _parse_path(self, path: str) -> list[str]:
        """
        Parse a dot-notation path into parts.

        Handles quoted keys like "Some Key".subkey
        """
        if not path:
            return []

        parts = []
        current = ""
        in_quotes = False

        i = 0
        while i < len(path):
            char = path[i]

            if char == '"':
                in_quotes = not in_quotes
                current += char
            elif char == "." and not in_quotes:
                if current:
                    parts.append(self._unquote_key(current))
                    current = ""
            else:
                current += char

            i += 1

        if current:
            parts.append(self._unquote_key(current))

        return parts

    def _unquote_key(self, key: str) -> str:
        """Remove quotes from a quoted key"""
        if key.startswith('"') and key.endswith('"'):
            return key[1:-1]
        return key

    def _deep_merge(self, base: Any, overlay: Any) -> Any:
        """
        Recursively merge two values.

        - Dicts are merged recursively
        - Lists are replaced (not merged)
        - Other types are replaced
        """
        if isinstance(base, dict) and isinstance(overlay, dict):
            result = base.copy()
            for key, value in overlay.items():
                if key in result:
                    result[key] = self._deep_merge(result[key], value)
                else:
                    result[key] = self._deep_copy(value)
            return result
        else:
            # Replace with overlay
            return self._deep_copy(overlay)

    def _deep_copy(self, obj: Any) -> Any:
        """Deep copy an object"""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj

    def __repr__(self) -> str:
        return f"Document({self._root})"
