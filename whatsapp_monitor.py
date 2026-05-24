"""
Project Configuration Module
Centralized settings for the WhatsApp MOJ Automation System
"""
import os
import json
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
BACKUPS_DIR = BASE_DIR / "backups"
CONFIG_DIR = BASE_DIR / "config"

# Ensure directories exist
for d in [DATA_DIR, LOGS_DIR, BACKUPS_DIR]:
    d.mkdir(exist_ok=True)

# Database
DB_PATH = DATA_DIR / "moj_automation.db"

# Excel
EXCEL_PATH = DATA_DIR / "moj_transactions.xlsx"
EXCEL_BACKUP_PATTERN = "moj_transactions_backup_{date}.xlsx"

# WhatsApp Web
WHATSAPP_URL = "https://web.whatsapp.com"
QR_TIMEOUT = 120  # seconds to wait for QR scan
MESSAGE_POLL_INTERVAL = 3  # seconds between message checks
RECONNECT_INTERVAL = 30  # seconds between reconnection attempts
MAX_RECONNECT_ATTEMPTS = 10

# Message Processing
PROCESSED_IDS_FILE = DATA_DIR / "processed_ids.json"
DUPLICATE_CHECK_WINDOW_DAYS = 7

# Regex Patterns
# Arabic pattern: يمكنكم دفع رسم طلبكم رقم {NUMBER} ... لـ: {NAME} {LINK}
ARABIC_PAYMENT_PATTERN = r"يمكنكم دفع رسم طلبكم رقم\s*(\d+).*?لـ:\s*([^\s].*?)\s+(https?://enotary\.moj\.gov\.ae/[^\s]+)"
# Fallback broader Arabic pattern
ARABIC_PAYMENT_PATTERN_FALLBACK = r"رقم\s*(\d+).*?(?:لـ|ل\s*):\s*([^
]+?)\s+(https?://[^\s]+)"

# English pattern: pay the fee for the Application number : {NUMBER} ... assigned to : {NAME} {LINK}
ENGLISH_PAYMENT_PATTERN = r"Application number\s*[:\s]\s*(\d+).*?assigned to\s*[:\s]\s*([^\s].*?)\s+(https?://enotary\.moj\.gov\.ae/[^\s]+)"
ENGLISH_PAYMENT_PATTERN_FALLBACK = r"Application number\s*[:\s]\s*(\d+).*?(?:assigned to|for)\s*[:\s]\s*([^
]+?)\s+(https?://[^\s]+)"

# Lawyer group pattern: extracts number from start of message
LAWYER_APP_PATTERN = r"^(\d+)\s+(.+)$"

# Group names (loaded from config file, these are defaults)
DEFAULT_GROUPS = {
    "payment_groups": [
        "MOJ Payments",
        "طلبات التوثيق",
        "E-Notary Requests"
    ],
    "broker_groups": [
        "Broker Deals",
        "وسطاء التوثيق"
    ],
    "internal_groups": [
        "اعتمادات",
        "Internal Approvals"
    ],
    "lawyer_mapping_group": "اعتمادات"
}

# Financial
DEFAULT_COMMISSION_PERCENT = 20.0
GROSS_AMOUNT_DEFAULT = 0.0  # Will be updated when payment is made

# UI
DASHBOARD_TITLE = "MOJ E-Notary Automation Dashboard"
DASHBOARD_WIDTH = 1400
DASHBOARD_HEIGHT = 900
THEME = "dark"
COLOR_THEME = "blue"

# Logging
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = "INFO"
LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5


def load_groups_config():
    """Load group configuration from JSON file"""
    config_file = CONFIG_DIR / "groups.json"
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_GROUPS.copy()


def save_groups_config(config):
    """Save group configuration to JSON file"""
    config_file = CONFIG_DIR / "groups.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


# Initialize default config if not exists
if not (CONFIG_DIR / "groups.json").exists():
    save_groups_config(DEFAULT_GROUPS)
