"""Tests for the per-extension file parser registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from mrag.data.parsers import (
    ParserError,
    UnsupportedExtensionError,
    parse_file,
    supported_extensions,
)


def test_supported_extensions_contains_core_formats() -> None:
    exts = set(supported_extensions())
    assert {"txt", "md", "csv", "pdf", "docx"}.issubset(exts)


def test_parse_txt(tmp_path: Path) -> None:
    path = tmp_path / "note.txt"
    path.write_text("Hello world.\nSecond line.", encoding="utf-8")

    docs = parse_file(path, "note.txt")
    assert len(docs) == 1
    assert "Hello world" in docs[0].text
    assert docs[0].source_filename == "note.txt"


def test_parse_md_strips_frontmatter_and_formatting(tmp_path: Path) -> None:
    path = tmp_path / "doc.md"
    path.write_text(
        "---\ntitle: x\n---\n# Heading\n\nSome **bold** text with `inline` code.\n",
        encoding="utf-8",
    )
    docs = parse_file(path, "doc.md")
    assert len(docs) == 1
    text = docs[0].text
    assert "title: x" not in text
    assert "**" not in text
    assert "bold" in text
    assert "inline" in text


def test_parse_csv_one_doc_per_row(tmp_path: Path) -> None:
    path = tmp_path / "data.csv"
    path.write_text(
        "title,body\nFoo,alpha\nBar,beta\n", encoding="utf-8"
    )
    docs = parse_file(path, "data.csv")
    assert len(docs) == 2
    assert "title: Foo" in docs[0].text
    assert "body: alpha" in docs[0].text
    assert docs[0].section == "row 1"
    assert docs[1].section == "row 2"


def test_parse_csv_skips_blank_rows(tmp_path: Path) -> None:
    path = tmp_path / "data.csv"
    path.write_text("a,b\nx,y\n,\n", encoding="utf-8")
    docs = parse_file(path, "data.csv")
    assert len(docs) == 1


def test_parse_docx_extracts_paragraphs(tmp_path: Path) -> None:
    docx_mod = pytest.importorskip("docx")
    path = tmp_path / "note.docx"
    doc = docx_mod.Document()
    doc.add_paragraph("First paragraph.")
    doc.add_paragraph("Second paragraph.")
    doc.save(str(path))

    docs = parse_file(path, "note.docx")
    assert len(docs) == 1
    assert "First paragraph." in docs[0].text
    assert "Second paragraph." in docs[0].text


def test_parse_unsupported_extension_raises(tmp_path: Path) -> None:
    path = tmp_path / "bad.xyz"
    path.write_text("ignored", encoding="utf-8")
    with pytest.raises(UnsupportedExtensionError):
        parse_file(path, "bad.xyz")


def test_parse_empty_file_raises(tmp_path: Path) -> None:
    path = tmp_path / "empty.txt"
    path.write_text("   \n", encoding="utf-8")
    with pytest.raises(ParserError):
        parse_file(path, "empty.txt")
