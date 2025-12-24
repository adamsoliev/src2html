#!/usr/bin/env python3
"""
src2html - Convert source code files to syntax-highlighted HTML.

Usage:
    python src2html.py <source_file> [--output <output.html>] [--open]
"""

import argparse
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


HTML_TEMPLATE = """<!DOCTYPE html>
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
        .header {{
            font-size: 12px;
            font-weight: normal;
            color: #333;
            padding: 4px 8px;
            border-bottom: 1px solid #ddd;
            background: #f8f8f8;
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
            }}
            .header {{
                padding: 2px 4px;
                border-bottom: 1px solid #ccc;
            }}
            .linenos {{
                padding: 0 4px 0 2px;
            }}
            .code {{
                padding-left: 4px;
            }}
        }}
        
        @page {{
            margin: 0.5cm;
        }}
        
        {pygments_css}
    </style>
</head>
<body>
    <div class="header">{title}</div>
    {code_html}
</body>
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


def highlight_with_pygments(code: str, filename: str) -> str:
    """Use Pygments to syntax highlight the code."""
    try:
        lexer = get_lexer_for_filename(filename)
    except:
        lexer = guess_lexer(code)
    
    formatter = HtmlFormatter(linenos=True, cssclass="highlight", lineanchors="line")
    return highlight(code, lexer, formatter)


def generate_html(source_path: Path) -> str:
    """Generate HTML from a source file."""
    code = source_path.read_text()
    
    if PYGMENTS_AVAILABLE:
        code_html = highlight_with_pygments(code, source_path.name)
    else:
        # Fallback: just wrap in pre/code tags
        import html
        escaped = html.escape(code)
        code_html = f'<div class="highlight"><pre><code>{escaped}</code></pre></div>'
    
    return HTML_TEMPLATE.format(
        title=source_path.name,
        pygments_css=CATPPUCCIN_CSS,
        code_html=code_html
    )


def main():
    parser = argparse.ArgumentParser(
        description="Convert source code to syntax-highlighted HTML"
    )
    parser.add_argument("source", help="Source file to convert")
    parser.add_argument(
        "-o", "--output", 
        help="Output HTML file (default: <source>.html)"
    )
    parser.add_argument(
        "--open", 
        action="store_true",
        help="Open the result in the default browser"
    )
    
    args = parser.parse_args()
    
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Error: File '{source_path}' not found", file=sys.stderr)
        sys.exit(1)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = source_path.with_suffix(".html")
    
    # Generate and write HTML
    html_content = generate_html(source_path)
    output_path.write_text(html_content)
    print(f"✓ Generated: {output_path}")
    
    # Optionally open in browser
    if args.open:
        webbrowser.open(f"file://{output_path.resolve()}")
        print("✓ Opened in browser")


if __name__ == "__main__":
    main()
