"""Formatting utilities for display values."""

from __future__ import annotations

from datetime import datetime, timezone


def format_bytes(num_bytes: int) -> str:
    """Convert a byte count to a human-readable string.

    Examples:
        format_bytes(0)          -> "0 B"
        format_bytes(1024)       -> "1.0 KB"
        format_bytes(4_300_000_000) -> "4.0 GB"
    """
    if num_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if abs(size) < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def format_relative_time(iso_str: str) -> str:
    """Convert an ISO 8601 timestamp to a relative time string.

    Examples:
        "2 minutes ago", "3 hours ago", "5 days ago"
    """
    if not iso_str:
        return "unknown"
    try:
        # Handle various ISO formats from Ollama
        dt_str = iso_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - dt
        seconds = int(delta.total_seconds())

        if seconds < 0:
            return "just now"
        if seconds < 60:
            return "just now"
        if seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        if seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        if seconds < 2_592_000:  # 30 days
            days = seconds // 86400
            return f"{days} day{'s' if days != 1 else ''} ago"
        if seconds < 31_536_000:  # 365 days
            months = seconds // 2_592_000
            return f"{months} month{'s' if months != 1 else ''} ago"
        years = seconds // 31_536_000
        return f"{years} year{'s' if years != 1 else ''} ago"
    except (ValueError, TypeError):
        return "unknown"


def truncate(text: str, max_len: int = 80) -> str:
    """Truncate text with an ellipsis if it exceeds max_len."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"
