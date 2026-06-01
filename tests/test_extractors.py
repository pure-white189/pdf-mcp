"""Tests for PDF MCP Server extractors.

Run with: pytest tests/test_extractors.py -v
Run from: pdf-mcp/ directory
"""
import sys
import os

# Add src to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
import pdfplumber
from detector import detect_page_type, detect_pdf_type
from extractors.text import extract_text_from_page


SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_pdfs")
SAMPLE_PDF = os.path.join(SAMPLE_DIR, "Lecture2_Exercise.pdf")


# ── detector tests ──

class TestDetectPageType:
    """Test single-page type detection."""

    def test_text_page(self):
        """A page with >50 chars and 0 images should be 'text'."""
        # Create a mock page object
        class MockPage:
            def extract_text(self):
                return "A" * 100
            images = []
        result = detect_page_type(MockPage())
        assert result["pagetype"] == "text"

    def test_mixed_page_with_text_and_image(self):
        """A page with >50 chars and >=1 image should be 'mixed'."""
        class MockPage:
            def extract_text(self):
                return "A" * 100
            images = ["img1"]
        result = detect_page_type(MockPage())
        assert result["pagetype"] == "mixed"

    def test_scanned_page(self):
        """A page with <=50 chars and >=2 images should be 'scanned'."""
        class MockPage:
            def extract_text(self):
                return "AB"
            images = ["img1", "img2"]
        result = detect_page_type(MockPage())
        assert result["pagetype"] == "scanned"

    def test_mixed_page_single_image(self):
        """A page with <=50 chars and 1 image should be 'mixed'."""
        class MockPage:
            def extract_text(self):
                return "AB"
            images = ["img1"]
        result = detect_page_type(MockPage())
        assert result["pagetype"] == "mixed"

    def test_blank_page(self):
        """A page with <=50 chars and 0 images should be 'blank'."""
        class MockPage:
            def extract_text(self):
                return ""
            images = []
        result = detect_page_type(MockPage())
        assert result["pagetype"] == "blank"

    def test_none_text(self):
        """A page where extract_text returns None should not crash."""
        class MockPage:
            def extract_text(self):
                return None
            images = []
        result = detect_page_type(MockPage())
        assert result["pagetype"] == "blank"


class TestDetectPdfType:
    """Test full PDF type detection with real file."""

    def test_real_pdf(self):
        """Detect type of sample PDF — should return 'mixed'."""
        result = detect_pdf_type(SAMPLE_PDF)
        assert result["doctype"] == "mixed"
        assert len(result["pages"]) == 31

    def test_nonexistent_file(self):
        """Opening a missing file should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot open PDF"):
            detect_pdf_type("/nonexistent/file.pdf")


# ── text extractor tests ──

class TestTextExtractor:
    """Test text extraction from a real PDF page."""

    def test_extract_first_page(self):
        """First page of sample PDF should contain 'Exercise'."""
        with pdfplumber.open(SAMPLE_PDF) as pdf:
            text = extract_text_from_page(pdf.pages[0])
        assert "Exercise" in text

    def test_extract_returns_string(self):
        """Result should always be a string, even for blank pages."""
        class MockPage:
            def extract_text(self):
                return None
        result = extract_text_from_page(MockPage())
        assert isinstance(result, str)

    def test_double_newlines_collapsed(self):
        """Double newlines should be collapsed to single."""
        class MockPage:
            def extract_text(self):
                return "line1\n\n\n\nline2"
        result = extract_text_from_page(MockPage())
        assert "\n\n" not in result


# ── formatter tests ──

class TestFormatter:
    """Test markdown_format page range logic."""

    def test_page_range(self):
        """Extracting pages 1-2 should return content for exactly 2 pages."""
        from formatter import markdown_format
        result = markdown_format(SAMPLE_PDF, start_page=1, end_page=2)
        assert "--- Page 1 ---" in result
        assert "--- Page 2 ---" in result
        assert "--- Page 3 ---" not in result

    def test_single_page(self):
        """Extracting a single page should work."""
        from formatter import markdown_format
        result = markdown_format(SAMPLE_PDF, start_page=1, end_page=1)
        assert "--- Page 1 ---" in result
        assert "--- Page 2 ---" not in result

    def test_invalid_start_page(self):
        """start_page beyond total pages should return error."""
        from formatter import markdown_format
        result = markdown_format(SAMPLE_PDF, start_page=999, end_page=1000)
        assert "Error" in result

    def test_nonexistent_file(self):
        """Missing file should return error string, not crash."""
        from formatter import markdown_format
        result = markdown_format("/nonexistent/file.pdf")
        assert "Error" in result
