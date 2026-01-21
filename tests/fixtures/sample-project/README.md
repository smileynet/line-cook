# Sample Project

A user registration system for testing Line Cook workflows.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from validation import validate_email, validate_password

# Validate user input
is_valid_email = validate_email("user@example.com")
is_strong_password = validate_password("SecurePass123!")
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |

## Development

Run tests:
```bash
pytest
```
