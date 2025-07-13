"""XSS Protection utilities"""

import html
import re
from typing import Any, Dict, Union


def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS"""
    if not isinstance(text, str):
        return str(text)

    # HTML escape
    text = html.escape(text)

    # Remove script tags
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL)

    # Remove javascript: URLs
    text = re.sub(r"javascript:", "", text, flags=re.IGNORECASE)

    # Remove onclick and other event handlers
    text = re.sub(r"on\w+\s*=", "", text, flags=re.IGNORECASE)

    return text.strip()


def validate_json_input(data: Union[Dict[str, Any], str, list]) -> Union[Dict[str, Any], str, list]:
    """Validate and sanitize JSON input recursively"""
    if isinstance(data, dict):
        return {key: validate_json_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [validate_json_input(item) for item in data]
    elif isinstance(data, str):
        return sanitize_input(data)
    else:
        return data


def secure_headers():
    """Return secure HTTP headers"""
    return {
        "Content-Type": "application/json",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-GovChat-Request",
    }
