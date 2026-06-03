# PDF MCP Server

A Model Context Protocol (MCP) server that lets Claude Code read PDF files reliably on Windows, solving the missing `pdftoppm` problem.

## How It Works

The server auto-detects each page's type and picks the best extraction strategy:

| Page Type | Strategy |
|-----------|----------|
| Text-heavy | pdfplumber direct extraction |
| Mixed (text + images) | pymupdf render + Claude vision AI |
| Scanned | tesseract OCR |
| Blank | Skipped |

## Prerequisites

- Windows with WSL (Ubuntu)
- Python 3.10+
- Claude Code CLI

## Installation

### 1. Set up WSL environment

```bash
# In WSL:
cd /mnt/g/claude\ code产品/pdf-mcp
python3 -m venv venv
source venv/bin/activate
pip install mcp pdfplumber pymupdf anthropic pytesseract Pillow
```

### 2. Install tesseract (for scanned PDFs)

```bash
sudo apt install tesseract-ocr tesseract-ocr-chi-sim
```

### 3. Configure Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://your-api-endpoint/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "your-api-key",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "your-model-name",
    "ANTHROPIC_VISION_MODEL": "your-vision-model"
  }
}
```

> `ANTHROPIC_VISION_MODEL` is optional — if not set, it falls back to `ANTHROPIC_DEFAULT_HAIKU_MODEL`.

Add to `~/.claude/.mcp.json`:

```json
{
  "mcpServers": {
    "pdf-reader": {
      "command": "wsl",
      "args": ["bash", "-c", "source ~/pdf-mcp/venv/bin/activate && cd '/mnt/g/claude code产品/pdf-mcp/src' && python server.py"]
    }
  }
}
```

### 4. Restart Claude Code

The server starts automatically when Claude Code launches.

## Tools

| Tool | Description |
|------|-------------|
| `pdf_extract(pdf_path)` | Extract all text from a PDF as Markdown |
| `pdf_extract_pages(pdf_path, start, end)` | Extract a page range (1-indexed) |
| `pdf_detect_type(pdf_path)` | Detect PDF type without extracting content |
| `pdf_extract_images(pdf_path, page)` | Extract and describe images on a page |

All paths support both formats:
- Windows: `G:\claude code产品\example.pdf`
- WSL: `/mnt/g/claude code产品/example.pdf`

Windows paths are automatically converted to WSL format.

## Running Tests

```bash
# In WSL:
source ~/pdf-mcp/venv/bin/activate
cd /mnt/g/claude\ code产品/pdf-mcp
python -m pytest tests/ -v
```

## Project Structure

```
pdf-mcp/
├── src/
│   ├── server.py           # MCP server entry point
│   ├── detector.py         # PDF page type detection
│   ├── formatter.py        # Markdown output + parallel extraction
│   ├── utils.py            # Shared helpers (render_page_to_image, normalize_path)
│   └── extractors/
│       ├── text.py         # pdfplumber text extraction
│       ├── vision.py       # pymupdf + Anthropic vision API
│       └── ocr.py          # tesseract OCR
├── tests/
│   ├── test_extractors.py  # pytest test suite
│   └── sample_pdfs/        # Test PDF files
└── README.md
```
