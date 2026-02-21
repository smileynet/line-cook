# Python Bookmark CLI

Command-line bookmark manager for Line Cook demo.

## Stack

- Python 3.8+, no external dependencies
- JSON file for persistence (`bookmarks.json`)
- unittest for testing

## Structure

```
bookmark.py          - BookmarkManager class and CLI entry point
test_bookmark.py     - Tests (run: python3 -m unittest test_bookmark -v)
bookmarks.json       - Data file (created automatically)
```

## Conventions

- Single-file app with BookmarkManager class
- Each bookmark: `{"id": str, "url": str, "title": str, "created_at": str}`
- IDs generated with UUID4 short prefix (first 8 chars)
- JSON file storage, loaded on start, saved after each mutation
- CLI uses argparse with subcommands: `add`, `list`, `delete`, `search`, `export`
- Bookmarks without explicit title default to the URL

## Commands

```bash
# Run tests
python3 -m unittest test_bookmark -v

# Usage (after implementation)
python3 bookmark.py add "https://example.com"
python3 bookmark.py add "https://python.org" --title "Python"
python3 bookmark.py list
python3 bookmark.py delete <id>
python3 bookmark.py search "python"
python3 bookmark.py export
python3 bookmark.py export output.json
```
