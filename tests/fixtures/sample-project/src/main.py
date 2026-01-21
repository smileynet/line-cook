#!/usr/bin/env python3
"""Main application entry point."""

from validation import validate_email, validate_password


def create_user(email: str, password: str) -> dict:
    """Create a new user with validated input."""
    if not validate_email(email):
        return {"error": "Invalid email format"}

    if not validate_password(password):
        return {"error": "Password too weak"}

    # TODO: Save to database
    return {"success": True, "email": email}


def main():
    """Run the application."""
    print("Sample Project v1.0")
    print("User registration system ready.")


if __name__ == "__main__":
    main()
