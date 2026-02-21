# Python Todo CLI

Command-line todo manager for Line Cook demo.

## Stack

- Python 3.8+, no external dependencies
- JSON file for persistence (`todos.json`)
- unittest for testing

## Structure

```
todo.py          - TodoApp class and CLI entry point
test_todo.py     - Tests (run: python3 -m pytest test_todo.py or python3 -m unittest test_todo)
todos.json       - Data file (created automatically)
```

## Conventions

- Single-file app with TodoApp class
- Each todo: `{"id": str, "text": str, "completed": bool, "created_at": str}`
- IDs generated with UUID4 short prefix (first 8 chars)
- JSON file storage, loaded on start, saved after each mutation
- CLI uses argparse with subcommands: `add`, `list`, `complete`

## Commands

```bash
# Run tests
python3 -m unittest test_todo -v

# Usage (after implementation)
python3 todo.py add "Buy groceries"
python3 todo.py list
python3 todo.py complete <id>
```
