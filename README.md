
<p align="center">
  <img src="assets/logo.png" alt="ctxbroker logo" width="160">
</p>

<h1 align="center">ctxbroker</h1>

<p align="center">
  <em>Lightweight code search for AI agents on Termux.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue" alt="Python">
  <img src="https://img.shields.io/badge/sqlite-FTS5-green" alt="SQLite FTS5">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="License">
</p>

---
# ctxbroker

![ctxbroker Logo Placeholder](https://via.placeholder.com/300x150?text=ctxbroker+logo)

**Lightweight Code Search Tool for Termux and Beyond**

A fast, efficient, and lightweight command-line tool for searching code snippets across your projects. Built with SQLite FTS5 for powerful full-text search capabilities.


## Features

- **Fast Search**: Uses SQLite FTS5 for blazing-fast code snippet search.
- **Cross-Platform**: Works on Termux and other Unix-like environments.
- **Lightweight**: Minimal dependencies, no complex setup.
- **Customizable**: Supports multiple file extensions for indexing.
- **Context-Aware**: Returns surrounding code context for each match.
- **JSON Output**: Results can be formatted as pretty JSON for easy parsing.


## Installation

### Prerequisites
- Python 3.6 or higher
- SQLite 3 (included by default in most Unix-like systems)

### Install via pip

```bash
pip install ctxbroker
```

### Install from Source

1. Clone the repository:

```bash
git clone https://github.com/Hatblack2002/ctxbroker.git
cd ctxbroker
```

2. Install in development mode:

```bash
pip install -e .
```


## Usage

### Initialize a Database

Initialize a database for a specific project:

```bash
ctxbroker init --project /path/to/project
```

### Index a Project

Index all supported file types in a project:

```bash
ctxbroker index --project /path/to/project
```

You can also specify custom file extensions:

```bash
ctxbroker index --project /path/to/project --ext .py .ts .js
```

### Rebuild Index

Rebuild the index for a project:

```bash
ctxbroker rebuild --project /path/to/project
```

### Search for Code Snippets

Search for code snippets in the indexed project:

```bash
ctxbroker query --project /path/to/project "search_term"
```

To limit the number of results:

```bash
ctxbroker query --project /path/to/project "search_term" --limit 5
```

To include more context lines:

```bash
ctxbroker query --project /path/to/project "search_term" --context 3
```

To get pretty JSON output:

```bash
ctxbroker query --project /path/to/project "search_term" --pretty
```


## Examples

### Example 1: Search for a Function Name

```bash
ctxbroker query --project /path/to/project "def my_function"
```

### Example 2: Search for a Class Definition

```bash
ctxbroker query --project /path/to/project "class MyClass"
```

### Example 3: Search for a Specific Import

```bash
ctxbroker query --project /path/to/project "import os"
```


## Output Format

The search results are returned in JSON format with the following structure:

```json
{
  "query": "search_term",
  "project": "/path/to/project",
  "total_matches": 5,
  "returned": 3,
  "tokens_estimated": 120,
  "results": [
    {
      "id": 1,
      "file": "/path/to/project/src/file.py",
      "line": 42,
      "snippet": "def my_function(x):",
      "context": {
        "before": ["# This is a comment"],
        "after": ["    return x * 2"]
      },
      "score": 0.95
    }
  ]
}
```


## License

This project is open-source and available under the MIT License.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
