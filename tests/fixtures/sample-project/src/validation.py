#!/usr/bin/env python3
"""Input validation utilities."""

import re


def validate_email(email: str) -> bool:
    """Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if valid email format
    """
    # TODO: Improve validation (tc-001)
    return "@" in email


def validate_password(password: str) -> bool:
    """Validate password strength.

    Args:
        password: Password to validate

    Returns:
        True if password meets requirements
    """
    # TODO: Add strength requirements (tc-001)
    return len(password) >= 4
