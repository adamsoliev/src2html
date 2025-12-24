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
python3 src2html.py <source_file_or_directory> [options]
```

**Options:**
- `-o, --output` - Output HTML file (default: `<source>.html` for files, `bundle.html` for directories)
- `--open` - Open the result in the default browser
- `--not-match-f PATTERN` - Exclude files containing this pattern in filename (supports comma-separated values or multiple flags)
- `--exclude-ext EXT` - Exclude files with this extension (supports comma-separated values or multiple flags)

## Examples

**Single file:**
```bash
python3 src2html.py main.cpp --open
```

**All files in directory:**
```bash
python3 src2html.py ./src --output output.html --open
```

**All files in `project` directory except files containing `test` or `backup` in filename and with `h` extension:**
```bash
python3 src2html.py ./project --not-match-f=test,backup --exclude-ext=h
```
