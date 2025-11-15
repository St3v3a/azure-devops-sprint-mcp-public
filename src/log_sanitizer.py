"""
Log sanitization utilities to prevent credential leakage.

This module provides functions to sanitize log messages and error strings
to prevent accidentally logging sensitive information like credentials,
tokens, and API keys.
"""

import re
from typing import Any


# Patterns that might indicate sensitive data
SENSITIVE_PATTERNS = [
    (re.compile(r'(password["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(client_secret["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(api_key["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(token["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(pat["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(bearer\s+)([a-zA-Z0-9\-._~+/]+=*)', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(authorization["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE), r'\1***REDACTED***'),
]


def sanitize_log_message(message: str) -> str:
    """
    Sanitize a log message by redacting sensitive information.

    This function removes or redacts common patterns that might contain
    sensitive data like passwords, tokens, and API keys.

    Args:
        message: The log message to sanitize

    Returns:
        Sanitized log message with sensitive data redacted
    """
    if not message:
        return message

    sanitized = message
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    return sanitized


def sanitize_error(error: Exception) -> str:
    """
    Sanitize an exception message for safe logging.

    Args:
        error: The exception to sanitize

    Returns:
        Sanitized error message
    """
    error_str = str(error)
    return sanitize_log_message(error_str)


def safe_log_error(error: Exception, context: str = "") -> str:
    """
    Create a safe error message for logging.

    This combines the context with the sanitized error message.

    Args:
        error: The exception
        context: Additional context (e.g., "Authentication failed")

    Returns:
        Safe error message for logging
    """
    sanitized_error = sanitize_error(error)
    error_type = type(error).__name__

    if context:
        return f"{context}: {error_type}: {sanitized_error}"
    else:
        return f"{error_type}: {sanitized_error}"
