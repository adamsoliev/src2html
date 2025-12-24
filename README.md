# src2html

Convert source code files to syntax-highlighted HTML.

100% vibe coded.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install pygments
```

## Usage

```bash
python src2html.py <source_file> [--output <output.html>] [--open]
```

**Options:**
- `-o, --output` - Output HTML file (default: `<source>.html`)
- `--open` - Open result in browser

## Example

```bash
python src2html.py main.cpp --open
```
