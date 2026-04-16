"""File parsers for user uploads.

Each parser converts a file on disk into one or more ParsedDocument
records carrying raw text plus provenance (source filename, section).
"""

from mrag.data.parsers.registry import (
    ParsedDocument,
    ParserError,
    UnsupportedExtensionError,
    parse_file,
    supported_extensions,
)

__all__ = [
    "ParsedDocument",
    "ParserError",
    "UnsupportedExtensionError",
    "parse_file",
    "supported_extensions",
]
