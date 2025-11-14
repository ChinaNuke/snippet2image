#!/usr/bin/env python3
"""
snippet2image - Convert code snippets to SVG/HTML with syntax highlighting and line numbers.
Generates SVG images with transparent background or standalone HTML snippets.
Supports highlighting specific lines with customizable colors.
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


def parse_line_ranges(line_spec):
    """
    Parse line range specification into a list of line numbers.

    Args:
        line_spec: Space-separated line numbers and ranges (e.g., "8-10 15 20-22")

    Returns:
        List of integers representing line numbers

    Examples:
        >>> parse_line_ranges("8 9 10")
        [8, 9, 10]
        >>> parse_line_ranges("8-10 15")
        [8, 9, 10, 15]
        >>> parse_line_ranges("1-3 5 7-9")
        [1, 2, 3, 5, 7, 8, 9]
    """
    if not line_spec:
        return []

    line_numbers = set()
    parts = line_spec.split()

    for part in parts:
        if '-' in part:
            # Handle range (e.g., "8-10")
            try:
                start, end = part.split('-', 1)
                start_line = int(start.strip())
                end_line = int(end.strip())
                if start_line > end_line:
                    raise ValueError(f"Invalid range: {part} (start > end)")
                line_numbers.update(range(start_line, end_line + 1))
            except ValueError as e:
                raise ValueError(f"Invalid line range '{part}': {e}")
        else:
            # Handle single line number
            try:
                line_numbers.add(int(part.strip()))
            except ValueError:
                raise ValueError(f"Invalid line number: {part}")

    return sorted(line_numbers)


def add_svg_highlights(svg_content, highlight_lines, highlight_color='#ffffcc'):
    """
    Add background highlights to specific lines in SVG output.

    Args:
        svg_content: The SVG content string from Pygments
        highlight_lines: List of line numbers to highlight (1-indexed)
        highlight_color: Background color for highlighted lines

    Returns:
        Modified SVG content with highlight rectangles
    """
    if not highlight_lines:
        return svg_content

    # Parse SVG to find text elements and their positions
    # SVG structure from Pygments has <text> elements with y coordinates for each line
    # We need to add <rect> elements before the highlighted lines

    # Find all line number text elements
    # Pygments SVG has 2 text elements per line: line number (with text-anchor="end") and code
    # We match only line number elements to get exactly one match per line
    text_pattern = r'<text[^>]+y="([^"]+)"[^>]+text-anchor="end"[^>]*>'
    matches = list(re.finditer(text_pattern, svg_content))

    if not matches:
        return svg_content

    # Extract font size from SVG to calculate rectangle dimensions
    font_size_match = re.search(r'font-size:\s*(\d+(?:\.\d+)?)', svg_content)
    font_size = float(font_size_match.group(1)) if font_size_match else 14

    # Calculate line height (typically 1.2-1.5 times font size in SVG)
    line_height = font_size * 1.2

    # Find the viewBox or svg width to determine rectangle width
    width_match = re.search(r'<svg[^>]+width="(\d+)"', svg_content)
    svg_width = int(width_match.group(1)) if width_match else 800

    # Build rectangles for highlighted lines
    rectangles = []
    for line_num in highlight_lines:
        if 0 < line_num <= len(matches):
            # Get the y position of the line (1-indexed to 0-indexed)
            match = matches[line_num - 1]
            y_pos = float(match.group(1))

            # Create rectangle that covers the entire line
            # Adjust y position to start above the text baseline
            rect_y = y_pos - font_size * 0.85  # Offset to align with text
            rect = (
                f'<rect x="0" y="{rect_y}" width="{svg_width}" '
                f'height="{line_height}" fill="{highlight_color}" '
                f'fill-opacity="0.3"/>'
            )
            rectangles.append((match.start(), rect))

    # Insert rectangles before their corresponding text elements
    # Work backwards to preserve string positions
    for pos, rect in sorted(rectangles, reverse=True):
        svg_content = svg_content[:pos] + rect + '\n' + svg_content[pos:]

    return svg_content


def code_to_image(code, output_file, format_type='svg', language=None,
                  style='monokai', font_name='monospace', font_size=14,
                  transparent=True, highlight_lines=None, highlight_color='#ffffcc'):
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
        highlight_lines: List of line numbers to highlight (1-indexed)
        highlight_color: Background color for highlighted lines (default: '#ffffcc')
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

        # Add width, height, and viewBox for proper display in image viewers
        line_count = len(code.split('\n'))
        longest_line = max(len(line) for line in code.split('\n'))

        # Calculate width based on code content
        # For monospace fonts: char_width ≈ 0.6 * font_size
        # Line numbers are at x=76, so: line_number_area + (chars * char_width) + padding
        char_width = font_size * 0.6
        svg_width = 76 + int(longest_line * char_width) + 40  # line numbers + code + right padding
        svg_height = line_count * (font_size + 5) + 20  # ystep + padding

        content = content.replace(
            '<svg xmlns="http://www.w3.org/2000/svg">',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">'
        )

        # Add line highlights if specified
        if highlight_lines:
            content = add_svg_highlights(content, highlight_lines, highlight_color)

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
            hl_lines=highlight_lines if highlight_lines else [],  # Add line highlighting
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

        # Apply custom highlight color if lines are highlighted
        if highlight_lines and highlight_color:
            # Replace the default highlight color with custom color
            # Pygments uses inline style "background-color: <color>" for highlighted lines
            content = re.sub(
                r'(<span[^>]*style="[^"]*?)background-color:\s*#[0-9a-fA-F]+',
                rf'\1background-color: {highlight_color}',
                content
            )

        # Make background transparent by replacing background color styles if requested
        # But preserve highlight colors
        if transparent:
            if highlight_lines:
                # Replace background colors but NOT in highlighted line spans
                # More precise: only replace on container divs and tables, not on highlight spans
                content = re.sub(
                    r'(<(?:div|table|td)[^>]*style="[^"]*?)background:\s*#[0-9a-fA-F]+',
                    r'\1background: transparent',
                    content
                )
            else:
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

  # Highlight specific lines (8 and 9)
  python snippet2image.py -i script.py -o output.svg --highlight-lines "8 9"

  # Highlight line ranges (lines 8-10 and 15)
  python snippet2image.py -i script.py -o output.html --highlight-lines "8-10 15"

  # Highlight with custom color
  python snippet2image.py -i script.py -o output.svg --highlight-lines "5-7" --highlight-color "#ff6b6b"

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
    parser.add_argument('--highlight-lines', type=str,
                       help='Lines to highlight (space-separated, supports ranges like "8-10 15 20-22")')
    parser.add_argument('--highlight-color', type=str, default='#ffffcc',
                       help='Background color for highlighted lines (default: #ffffcc - light yellow)')
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

    # Parse highlight lines if provided
    highlight_lines = None
    if args.highlight_lines:
        try:
            highlight_lines = parse_line_ranges(args.highlight_lines)
        except ValueError as e:
            print(f"Error parsing highlight lines: {e}", file=sys.stderr)
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
            transparent=not args.opaque_background,
            highlight_lines=highlight_lines,
            highlight_color=args.highlight_color
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
