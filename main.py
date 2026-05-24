"""
Helper Utilities Module
Common utility functions used across the project
"""
import re
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import arabic_reshaper
from bidi.algorithm import get_display


def generate_message_id(message_text: str, timestamp: str, sender: str) -> str:
    """
    Generate unique message ID based on content hash

    Args:
        message_text: Message content
        timestamp: Message timestamp string
        sender: Sender name

    Returns:
        Unique hash string
    """
    content = f"{message_text}|{timestamp}|{sender}"
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def detect_language(text: str) -> str:
    """
    Detect if text is primarily Arabic or English

    Args:
        text: Input text

    Returns:
        'arabic' or 'english'
    """
    arabic_chars = len(re.findall(r'[؀-ۿ]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))

    return "arabic" if arabic_chars > english_chars else "english"


def reshape_arabic_text(text: str) -> str:
    """
    Reshape Arabic text for proper display (RTL support)

    Args:
        text: Arabic text

    Returns:
        Reshaped text for display
    """
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


def parse_whatsapp_timestamp(ts_text: str) -> Optional[datetime]:
    """
    Parse WhatsApp timestamp to datetime object

    Args:
        ts_text: Timestamp string from WhatsApp

    Returns:
        datetime object or None
    """
    formats = [
        "%H:%M, %m/%d/%Y",
        "%I:%M %p, %m/%d/%Y",
        "%H:%M",
        "%I:%M %p",
        "%Y-%m-%d %H:%M:%S"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(ts_text.strip(), fmt)
        except ValueError:
            continue

    # If only time provided, assume today
    try:
        today = datetime.now().date()
        for fmt in ["%H:%M", "%I:%M %p"]:
            try:
                t = datetime.strptime(ts_text.strip(), fmt).time()
                return datetime.combine(today, t)
            except ValueError:
                continue
    except Exception:
        pass

    return None


def load_processed_ids(file_path: Path) -> set:
    """
    Load set of processed message IDs from JSON file

    Args:
        file_path: Path to processed IDs file

    Returns:
        Set of message IDs
    """
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("ids", []))
        except Exception:
            return set()
    return set()


def save_processed_ids(file_path: Path, ids: set):
    """
    Save processed message IDs to JSON file

    Args:
        file_path: Path to processed IDs file
        ids: Set of message IDs
    """
    data = {
        "ids": list(ids),
        "last_updated": datetime.now().isoformat()
    }
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def clean_text(text: str) -> str:
    """
    Clean and normalize text

    Args:
        text: Raw text

    Returns:
        Cleaned text
    """
    if not text:
        return ""
    # Remove zero-width characters
    text = re.sub(r'[​-‏﻿]', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def is_broker_group(group_name: str, broker_groups: list) -> bool:
    """
    Check if group is a broker group

    Args:
        group_name: WhatsApp group name
        broker_groups: List of broker group names

    Returns:
        True if broker group
    """
    return any(bg.lower() in group_name.lower() or group_name.lower() in bg.lower() 
               for bg in broker_groups)


def format_currency(amount: float, currency: str = "AED") -> str:
    """
    Format amount as currency string

    Args:
        amount: Numeric amount
        currency: Currency code

    Returns:
        Formatted currency string
    """
    return f"{amount:,.2f} {currency}"


def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Truncate text with ellipsis

    Args:
        text: Input text
        max_length: Maximum length

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
