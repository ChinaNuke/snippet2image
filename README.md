# snippet2image

Convert code snippets to SVG or HTML with syntax highlighting and line numbers.

## Features

- 🎨 Syntax highlighting with 49+ color themes
- 🔢 Line numbers included
- 🌐 Output as SVG or HTML
- 🔍 Auto-detect programming language
- 🎭 Transparent or opaque backgrounds
- 📝 Works with stdin or files

## Installation

```bash
git clone <repository-url>
cd snippet2image
uv sync
```

## Quick Start

```bash
# From file to SVG
uv run python snippet2image.py -i script.py -o output.svg

# From stdin to HTML
cat code.js | uv run python snippet2image.py -o output.html -l javascript

# With custom theme
uv run python snippet2image.py -i code.py -o output.svg -s github-dark
```

## Usage

```bash
snippet2image -i INPUT -o OUTPUT [options]
```

### Options

- `-i, --input` - Input file (or use stdin)
- `-o, --output` - Output file (.svg or .html)
- `-l, --language` - Programming language (auto-detect if omitted)
- `-s, --style` - Color theme (default: monokai)
- `-f, --format` - Force format: svg or html
- `--opaque-background` - Use theme's background color instead of transparent
- `--font` - Font family (default: monospace)
- `--font-size` - Font size in pixels (default: 14)
- `--list-styles` - Show all available themes

## Available Themes

View all 49 styles:
```bash
uv run python snippet2image.py --list-styles
```

Popular themes: `monokai`, `github-dark`, `dracula`, `one-dark`, `vim`, `solarized-dark`

Preview themes at: https://pygments.org/demo/

## Examples

### SVG Output
![SVG Demo](demos/demo.svg)

### HTML Output
See [demo.html](demos/demo.html) for an interactive example.

## Use Cases

- 📚 Documentation and tutorials
- 🎨 Blog posts with code examples
- 🖼️ Presentations and slides
- 🎯 Draw.io diagrams (HTML format)
- 📱 README files with syntax highlighting

## Requirements

- Python 3.13+
- pygments

## License

MIT
