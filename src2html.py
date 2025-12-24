#!/usr/bin/env python3
"""
src2html - Convert source code files to syntax-highlighted HTML.

Usage:
    Single file:
        python src2html.py <source_file> [--output <output.html>] [--open]
    
    Directory (multi-file):
        python src2html.py <directory> [--not-match-f=<pattern>] [--exclude-ext=<ext>] [--output <output.html>] [--open]
"""

import argparse
import fnmatch
import re
import subprocess
import sys
import webbrowser
from pathlib import Path

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_for_filename, guess_lexer
    from pygments.formatters import HtmlFormatter
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False


# Common source file extensions to include
SOURCE_EXTENSIONS = {
    'py', 'js', 'ts', 'jsx', 'tsx', 'c', 'cc', 'cpp', 'h', 'hpp',
    'java', 'go', 'rs', 'rb', 'php', 'swift', 'kt', 'scala',
    'sh', 'bash', 'zsh', 'fish', 'ps1',
    'html', 'css', 'scss', 'sass', 'less',
    'json', 'yaml', 'yml', 'toml', 'xml',
    'sql', 'md', 'rst', 'txt',
    'lua', 'r', 'pl', 'pm', 'hs', 'ml', 'ex', 'exs',
    'vue', 'svelte', 'astro',
    'dockerfile', 'makefile', 'cmake',
}


HTML_HEADER = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', monospace;
            font-size: 13px;
            line-height: 1.4;
            background: #fff;
            color: #000;
            padding-left: 16px;
        }}
        
        /* Table of Contents */
        .toc {{
            padding: 16px;
            background: #f8f8f8;
            border-bottom: 1px solid #ddd;
            margin-bottom: 16px;
        }}
        .toc h2 {{
            font-size: 14px;
            margin-bottom: 8px;
            color: #333;
        }}
        .toc ul {{
            list-style: none;
        }}
        .toc li {{
            margin-bottom: 4px;
        }}
        .toc a {{
            color: #0066cc;
            text-decoration: none;
            font-size: 12px;
        }}
        .toc a:hover {{
            text-decoration: underline;
        }}
        
        /* File sections */
        .file-section {{
            margin-bottom: 24px;
        }}
        .file-header {{
            font-size: 14px;
            font-weight: bold;
            color: #000;
            padding: 8px 12px;
            border-bottom: 1px solid #ccc;
            background: #e0e0e0;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}
        .highlight {{
            background: #fff;
        }}
        .highlight pre {{
            margin: 0;
            white-space: pre;
        }}
        .highlighttable {{
            border-collapse: collapse;
            width: 100%;
        }}
        .highlighttable td {{
            padding: 0;
            vertical-align: top;
        }}
        .highlighttable td.linenos {{
            background: #f8f8f8;
            color: #999;
            text-align: right;
            padding: 0 5px 0 4px;
            user-select: none;
            border-right: 1px solid #eee;
        }}
        .linenos pre {{
            margin: 0;
        }}
        .highlighttable td.code {{
            padding-left: 10px;
        }}
        .code pre {{
            margin: 0;
        }}
        
        /* Print styles */
        @media print {{
            body {{
                font-size: 10px;
                padding-left: 0;
            }}
            .toc {{
                page-break-after: always;
            }}
            .file-section {{
                page-break-before: always;
            }}
            .file-section:first-of-type {{
                page-break-before: avoid;
            }}
            .file-header {{
                font-size: 12px;
                padding: 6px 8px;
                background: #d0d0d0;
                border-bottom: 2px solid #999;
            }}
            .linenos {{
                padding: 0 4px 0 2px;
            }}
            .code {{
                padding-left: 4px;
            }}
        }}
        
        @page {{
            size: A4;
            margin: 0.7cm 0.7cm 1.5cm 0.7cm;
            @bottom-center {{
                content: counter(page);
            }}
        }}
        
        {pygments_css}
    </style>
</head>
<body>
"""

HTML_FOOTER = """</body>
</html>
"""

# Clean light theme syntax colors (print-friendly)
CATPPUCCIN_CSS = """
.highlight .hll { background-color: #ffffcc }
.highlight .c { color: #6a737d } /* Comment */
.highlight .k { color: #d73a49 } /* Keyword */
.highlight .n { color: #24292e } /* Name */
.highlight .o { color: #24292e } /* Operator */
.highlight .p { color: #24292e } /* Punctuation */
.highlight .cm { color: #6a737d } /* Comment.Multiline */
.highlight .cp { color: #d73a49 } /* Comment.Preproc */
.highlight .c1 { color: #6a737d } /* Comment.Single */
.highlight .cs { color: #6a737d } /* Comment.Special */
.highlight .gd { color: #b31d28; background-color: #ffeef0 } /* Generic.Deleted */
.highlight .ge { font-style: italic } /* Generic.Emph */
.highlight .gi { color: #22863a; background-color: #f0fff4 } /* Generic.Inserted */
.highlight .gs { font-weight: bold } /* Generic.Strong */
.highlight .gu { color: #6f42c1 } /* Generic.Subheading */
.highlight .kc { color: #d73a49 } /* Keyword.Constant */
.highlight .kd { color: #d73a49 } /* Keyword.Declaration */
.highlight .kn { color: #d73a49 } /* Keyword.Namespace */
.highlight .kp { color: #d73a49 } /* Keyword.Pseudo */
.highlight .kr { color: #d73a49 } /* Keyword.Reserved */
.highlight .kt { color: #d73a49 } /* Keyword.Type */
.highlight .m { color: #005cc5 } /* Literal.Number */
.highlight .s { color: #032f62 } /* Literal.String */
.highlight .na { color: #6f42c1 } /* Name.Attribute */
.highlight .nb { color: #005cc5 } /* Name.Builtin */
.highlight .nc { color: #6f42c1 } /* Name.Class */
.highlight .no { color: #005cc5 } /* Name.Constant */
.highlight .nd { color: #6f42c1 } /* Name.Decorator */
.highlight .ni { color: #24292e } /* Name.Entity */
.highlight .ne { color: #d73a49 } /* Name.Exception */
.highlight .nf { color: #6f42c1 } /* Name.Function */
.highlight .nl { color: #24292e } /* Name.Label */
.highlight .nn { color: #6f42c1 } /* Name.Namespace */
.highlight .nt { color: #22863a } /* Name.Tag */
.highlight .nv { color: #e36209 } /* Name.Variable */
.highlight .ow { color: #d73a49 } /* Operator.Word */
.highlight .w { color: #24292e } /* Text.Whitespace */
.highlight .mf { color: #005cc5 } /* Literal.Number.Float */
.highlight .mh { color: #005cc5 } /* Literal.Number.Hex */
.highlight .mi { color: #005cc5 } /* Literal.Number.Integer */
.highlight .mo { color: #005cc5 } /* Literal.Number.Oct */
.highlight .sb { color: #032f62 } /* Literal.String.Backtick */
.highlight .sc { color: #032f62 } /* Literal.String.Char */
.highlight .sd { color: #032f62 } /* Literal.String.Doc */
.highlight .s2 { color: #032f62 } /* Literal.String.Double */
.highlight .se { color: #005cc5 } /* Literal.String.Escape */
.highlight .sh { color: #032f62 } /* Literal.String.Heredoc */
.highlight .si { color: #005cc5 } /* Literal.String.Interpol */
.highlight .sx { color: #032f62 } /* Literal.String.Other */
.highlight .sr { color: #032f62 } /* Literal.String.Regex */
.highlight .s1 { color: #032f62 } /* Literal.String.Single */
.highlight .ss { color: #005cc5 } /* Literal.String.Symbol */
.highlight .bp { color: #005cc5 } /* Name.Builtin.Pseudo */
.highlight .vc { color: #e36209 } /* Name.Variable.Class */
.highlight .vg { color: #e36209 } /* Name.Variable.Global */
.highlight .vi { color: #e36209 } /* Name.Variable.Instance */
.highlight .il { color: #005cc5 } /* Literal.Number.Integer.Long */
"""


def collect_files(directory: Path, not_match_patterns: list[str], exclude_extensions: list[str]) -> list[Path]:
    """
    Recursively collect source files from a directory, applying filters.
    
    Args:
        directory: The directory to scan
        not_match_patterns: Patterns to exclude from filenames (substring match)
        exclude_extensions: File extensions to exclude (without dot)
    
    Returns:
        Sorted list of file paths
    """
    # Directories to always ignore
    ignored_dirs = {
        'venv', '.venv', 'env', '.env',
        'node_modules', 
        '__pycache__', '.pytest_cache', '.mypy_cache',
        '.git', '.svn', '.hg',
        'dist', 'build', '.build',
        'target',  # Rust/Java
        'vendor',  # Go/PHP
    }
    
    files = []
    exclude_ext_set = {ext.lower().lstrip('.') for ext in exclude_extensions}
    
    for file_path in directory.rglob('*'):
        if not file_path.is_file():
            continue
        
        # Skip hidden files and directories
        if any(part.startswith('.') for part in file_path.parts):
            continue
        
        # Skip ignored directories
        if any(part in ignored_dirs for part in file_path.parts):
            continue
        
        # Get extension (handle files like Makefile, Dockerfile)
        ext = file_path.suffix.lower().lstrip('.')
        if not ext:
            # Check if it's a known extensionless file
            name_lower = file_path.name.lower()
            if name_lower in ('makefile', 'dockerfile', 'rakefile', 'gemfile'):
                ext = name_lower
            else:
                continue
        
        # Check if extension is in our source file list
        if ext not in SOURCE_EXTENSIONS:
            continue
        
        # Apply extension exclusion
        if ext in exclude_ext_set:
            continue
        
        # Apply filename pattern exclusion
        filename = file_path.name
        if any(pattern in filename for pattern in not_match_patterns):
            continue
        
        files.append(file_path)
    
    # Sort alphabetically by relative path
    files.sort(key=lambda p: str(p.relative_to(directory)).lower())
    
    return files


def highlight_with_pygments(code: str, filename: str, anchor_prefix: str = "line") -> str:
    """Use Pygments to syntax highlight the code."""
    try:
        lexer = get_lexer_for_filename(filename)
    except:
        lexer = guess_lexer(code)
    
    formatter = HtmlFormatter(linenos=True, cssclass="highlight", lineanchors=anchor_prefix)
    return highlight(code, lexer, formatter)


def generate_file_section(file_path: Path, file_index: int, base_dir: Path = None) -> str:
    """Generate HTML for a single file section."""
    code = file_path.read_text()
    
    # Use relative path for display if base_dir provided
    if base_dir:
        display_name = str(file_path.relative_to(base_dir))
    else:
        display_name = file_path.name
    
    # Generate syntax-highlighted code with unique anchor prefix
    anchor_prefix = f"file{file_index}-line"
    
    if PYGMENTS_AVAILABLE:
        code_html = highlight_with_pygments(code, file_path.name, anchor_prefix)
    else:
        import html
        escaped = html.escape(code)
        code_html = f'<div class="highlight"><pre><code>{escaped}</code></pre></div>'
    
    return f'''<div class="file-section" id="file-{file_index}">
    <div class="file-header">{display_name}</div>
    {code_html}
</div>
'''


def generate_toc(files: list[Path], base_dir: Path) -> str:
    """Generate table of contents HTML."""
    items = []
    for i, file_path in enumerate(files):
        display_name = str(file_path.relative_to(base_dir))
        items.append(f'<li><a href="#file-{i}">{display_name}</a></li>')
    
    return f'''<div class="toc">
    <h2>Table of Contents</h2>
    <ul>
        {"".join(items)}
    </ul>
</div>
'''


def generate_single_html(source_path: Path) -> str:
    """Generate HTML from a single source file (original behavior)."""
    code = source_path.read_text()
    
    if PYGMENTS_AVAILABLE:
        code_html = highlight_with_pygments(code, source_path.name)
    else:
        import html
        escaped = html.escape(code)
        code_html = f'<div class="highlight"><pre><code>{escaped}</code></pre></div>'
    
    html_content = HTML_HEADER.format(
        title=source_path.name,
        pygments_css=CATPPUCCIN_CSS
    )
    html_content += f'<div class="file-header">{source_path.name}</div>\n'
    html_content += code_html
    html_content += HTML_FOOTER
    
    return html_content


def generate_multi_html(files: list[Path], base_dir: Path, title: str) -> str:
    """Generate HTML from multiple source files."""
    html_content = HTML_HEADER.format(
        title=title,
        pygments_css=CATPPUCCIN_CSS
    )
    
    # Add table of contents
    html_content += generate_toc(files, base_dir)
    
    # Add each file section
    for i, file_path in enumerate(files):
        html_content += generate_file_section(file_path, i, base_dir)
    
    html_content += HTML_FOOTER
    
    return html_content


def main():
    parser = argparse.ArgumentParser(
        description="Convert source code to syntax-highlighted HTML"
    )
    parser.add_argument("source", help="Source file or directory to convert")
    parser.add_argument(
        "-o", "--output", 
        help="Output HTML file (default: <source>.html or bundle.html for directories)"
    )
    parser.add_argument(
        "--open", 
        action="store_true",
        help="Open the result in the default browser"
    )
    parser.add_argument(
        "--not-match-f",
        dest="not_match_f",
        action="append",
        default=[],
        help="Exclude files containing this pattern in filename (can be used multiple times)"
    )
    parser.add_argument(
        "--exclude-ext",
        dest="exclude_ext",
        action="append",
        default=[],
        help="Exclude files with this extension (can be used multiple times)"
    )
    
    args = parser.parse_args()
    
    # Expand comma-separated values in filter options
    def expand_comma_separated(items: list[str]) -> list[str]:
        result = []
        for item in items:
            result.extend(part.strip() for part in item.split(',') if part.strip())
        return result
    
    args.not_match_f = expand_comma_separated(args.not_match_f)
    args.exclude_ext = expand_comma_separated(args.exclude_ext)
    
    source_path = Path(args.source).resolve()
    
    if not source_path.exists():
        print(f"Error: '{source_path}' not found", file=sys.stderr)
        sys.exit(1)
    
    if source_path.is_file():
        # Single file mode (original behavior)
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = source_path.with_suffix(".html")
        
        html_content = generate_single_html(source_path)
        output_path.write_text(html_content)
        print(f"✓ Generated: {output_path}")
    
    else:
        # Directory mode (multi-file)
        files = collect_files(source_path, args.not_match_f, args.exclude_ext)
        
        if not files:
            print("Error: No source files found", file=sys.stderr)
            sys.exit(1)
        
        print(f"Found {len(files)} files:")
        for f in files:
            print(f"  - {f.relative_to(source_path)}")
        
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = source_path / "bundle.html"
        
        title = f"{source_path.name} - Source Code"
        html_content = generate_multi_html(files, source_path, title)
        output_path.write_text(html_content)
        print(f"✓ Generated: {output_path}")
    
    # Optionally open in browser
    if args.open:
        webbrowser.open(f"file://{output_path.resolve()}")
        print("✓ Opened in browser")


if __name__ == "__main__":
    main()
