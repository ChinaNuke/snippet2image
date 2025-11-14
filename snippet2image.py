#!/usr/bin/env python3
"""
snippet2image - Convert code snippets to SVG/HTML with syntax highlighting and line numbers.
Generates SVG images with transparent background or standalone HTML snippets.
"""

import sys
import argparse
import os
import re
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import SvgFormatter, HtmlFormatter
from pygments.styles import get_all_styles
from pygments.util import ClassNotFound


def code_to_image(code, output_file, format_type='svg', language=None,
                  style='monokai', font_name='monospace', font_size=14,
                  transparent=True):
    """
    Convert code snippet to SVG or HTML with syntax highlighting and line numbers.

    Args:
        code: Source code string
        output_file: Output file path
        format_type: Output format ('svg' or 'html')
        language: Programming language (auto-detect if None)
        style: Pygments style name
        font_name: Font family for the code
        font_size: Font size in pixels
        transparent: Make background transparent (default: True)
    """
    # Get lexer for syntax highlighting
    if language:
        try:
            lexer = get_lexer_by_name(language, stripall=True)
        except ClassNotFound:
            print(f"Warning: Unknown language '{language}', attempting auto-detection")
            lexer = guess_lexer(code)
    else:
        lexer = guess_lexer(code)

    if format_type.lower() == 'svg':
        # Create SVG formatter with line numbers and transparent background
        formatter = SvgFormatter(
            style=style,
            linenos=True,
            fontfamily=font_name,
            fontsize=f"{font_size}px",
            cssclass="highlight"
        )

        # Generate SVG
        content = highlight(code, lexer, formatter)

        # Remove background from SVG (make transparent) if requested
        if transparent:
            content = content.replace('background: #', 'background: transparent; /* #')

    elif format_type.lower() == 'html':
        # Create HTML formatter with line numbers (no full document for draw.io compatibility)
        formatter = HtmlFormatter(
            style=style,
            linenos=True,
            full=False,  # Generate just the code block, not full HTML document
            noclasses=True,  # Use inline styles instead of CSS classes
            fontfamily=font_name,
            fontsize=f"{font_size}px",
        )

        # Generate HTML
        content = highlight(code, lexer, formatter)

        # Fix line number alignment by adding matching line-height to line numbers
        # The code section has line-height: 125%, so line numbers need the same
        content = re.sub(
            r'(<td class="linenos">.*?<pre)>',
            r'\1 style="line-height: 125%;">',
            content,
            flags=re.DOTALL
        )

        # Make background transparent by replacing background color styles if requested
        if transparent:
            content = re.sub(r'background:\s*#[0-9a-fA-F]+', 'background: transparent', content)

    else:
        raise ValueError(f"Unsupported format: {format_type}")

    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"{format_type.upper()} saved to: {output_file}")
    print(f"Language: {lexer.name}")
    print(f"Style: {style}")


def list_styles():
    """List all available Pygments styles."""
    styles = sorted(get_all_styles())
    print(f"Available styles ({len(styles)} total):")
    print()
    for i, style in enumerate(styles, 1):
        print(f"  {i:2}. {style}")
    print()
    print("Preview styles at: https://pygments.org/demo/")


def main():
    parser = argparse.ArgumentParser(
        description='Convert code snippets to SVG or HTML with syntax highlighting and line numbers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available styles
  python snippet2image.py --list-styles

  # Generate SVG from stdin with a specific style
  cat script.py | python snippet2image.py -o output.svg -l python -s github-dark

  # Generate HTML from file (transparent background by default)
  python snippet2image.py -i script.py -o output.html -l python

  # Generate with opaque background
  python snippet2image.py -i script.py -o output.svg --opaque-background

  # Auto-detect format from extension
  python snippet2image.py -i script.js -o output.svg

Popular styles: monokai, github-dark, dracula, one-dark, vim, solarized-dark, etc.
Preview styles at: https://pygments.org/demo/
        """
    )

    parser.add_argument('-i', '--input', type=str,
                       help='Input file (if not provided, reads from stdin)')
    parser.add_argument('-o', '--output', type=str,
                       help='Output file path (.svg or .html)')
    parser.add_argument('-f', '--format', type=str, choices=['svg', 'html'],
                       help='Output format (auto-detect from extension if not specified)')
    parser.add_argument('-l', '--language', type=str,
                       help='Programming language (auto-detect if not specified)')
    parser.add_argument('-s', '--style', type=str, default='monokai',
                       help='Pygments style name (default: monokai)')
    parser.add_argument('--font', type=str, default='monospace',
                       help='Font family (default: monospace)')
    parser.add_argument('--font-size', type=int, default=14,
                       help='Font size in pixels (default: 14)')
    parser.add_argument('--opaque-background', action='store_true',
                       help='Use opaque background instead of transparent (default: transparent)')
    parser.add_argument('--list-styles', action='store_true',
                       help='List all available styles and exit')

    args = parser.parse_args()

    # Handle --list-styles
    if args.list_styles:
        list_styles()
        sys.exit(0)

    # Validate output is required
    if not args.output:
        parser.error('the following arguments are required: -o/--output')

    # Determine format
    if args.format:
        format_type = args.format
    else:
        # Auto-detect from file extension
        _, ext = os.path.splitext(args.output)
        if ext.lower() == '.html':
            format_type = 'html'
        elif ext.lower() == '.svg':
            format_type = 'svg'
        else:
            print("Warning: Unknown extension, defaulting to SVG")
            format_type = 'svg'

    # Read input
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            code = f.read()
    else:
        if sys.stdin.isatty():
            print("Enter your code (press Ctrl+D when finished):")
        code = sys.stdin.read()

    if not code.strip():
        print("Error: No code provided", file=sys.stderr)
        sys.exit(1)

    # Convert to specified format
    try:
        code_to_image(
            code=code,
            output_file=args.output,
            format_type=format_type,
            language=args.language,
            style=args.style,
            font_name=args.font,
            font_size=args.font_size,
            transparent=not args.opaque_background
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
