# 🏛️ MOJ E-Notary WhatsApp Automation System

A professional Windows desktop automation system that monitors WhatsApp Web groups for UAE Ministry of Justice (MOJ) e-Notary payment requests, automatically extracts transaction data, matches lawyers, and maintains financial records in Excel.

---

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Regex Patterns](#regex-patterns)
- [Dashboard](#dashboard)
- [Future Upgrades](#future-upgrades)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## ✨ Features

### WhatsApp Monitoring
- ✅ Monitors multiple WhatsApp Web groups simultaneously
- ✅ Reads only new incoming messages (no duplicates)
- ✅ Saves processed message IDs locally
- ✅ Auto-reconnects if WhatsApp disconnects
- ✅ Multi-threaded monitoring for performance

### Payment Message Extraction
- ✅ Supports **Arabic** and **English** payment messages
- ✅ Primary: High-speed REGEX parsing
- ✅ Fallback: AI heuristic parser when regex fails
- ✅ Extracts: Application Number, Client Name, Payment Link, Group, Timestamp, Language

### Lawyer Matching System
- ✅ Monitors lawyer approval group ("اعتمادات")
- ✅ Maps Application Number → Lawyer Name automatically
- ✅ Stores mappings in SQLite database
- ✅ Auto-assigns lawyers to payment transactions

### Excel System
- ✅ Master Excel sheet with all transaction data
- ✅ Auto-append new rows (duplicate prevention)
- ✅ Auto-calculate: Gross, Commission (20%), Net amounts
- ✅ Auto-backup Excel file daily
- ✅ Professional formatting with color-coded headers
- ✅ Summary sheets: By Lawyer, By Group

### Dashboard
- ✅ Real-time statistics display
- ✅ Total transactions today / all time
- ✅ Transactions per lawyer / per group
- ✅ Broker commissions tracking
- ✅ Pending unmatched transactions view
- ✅ Manual lawyer assignment for unmatched items
- ✅ Connection status indicator
- ✅ System logs viewer

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WhatsApp Web (Browser)                    │
│                   ┌─────────────────┐                        │
│                   │  Selenium       │                        │
│                   │  WebDriver      │                        │
│                   └────────┬────────┘                        │
└────────────────────────────┼────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Message Parser │
                    │  (Regex + AI)   │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
    ┌───────▼──────┐ ┌──────▼──────┐ ┌───────▼──────┐
    │ Lawyer       │ │ Transaction │ │  Processed  │
    │ Matcher      │ │ Database    │ │  IDs Store  │
    └───────┬──────┘ └──────┬──────┘ └─────────────┘
            │               │
            └───────┬───────┘
                    │
            ┌───────▼────────┐
            │ Excel Manager  │
            │ (openpyxl)     │
            └───────┬────────┘
                    │
            ┌───────▼────────┐
            │   Dashboard    │
            │ (CustomTkinter)│
            └────────────────┘
```

---

## 🚀 Installation

### Prerequisites
- Windows 10/11
- Python 3.9+
- Google Chrome browser
- WhatsApp account with active groups

### Step 1: Clone or Download
```bash
cd whatsapp_moj_automation
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Install ChromeDriver (Auto)
The system uses `webdriver-manager` which automatically downloads the correct ChromeDriver.

---

## ⚙️ Configuration

### Edit `config/groups.json`

```json
{
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
    "lawyer_mapping_group": "اعتمادات",
    "commission_percent": 20.0
}
```

### Group Types Explained

| Type | Purpose | Example Messages |
|------|---------|-----------------|
| **Payment Groups** | Where MOJ payment links are posted | "pay the fee for Application number : 668717..." |
| **Broker Groups** | Broker-mediated transactions (20% commission) | Same format as payment groups |
| **Internal Groups** | Office management | Various internal communications |
| **Lawyer Group** | Lawyer-application mappings | "681476 انجليزي" |

---

## 🖥️ Usage

### First Run (Setup Mode)
```bash
python main.py
```

1. A Chrome window will open with WhatsApp Web
2. **Scan the QR code** with your phone's WhatsApp
3. The system will save your session for future runs
4. The dashboard will appear

### Headless Mode (After First Login)
```bash
python main.py --headless --no-ui
```

### With Custom Config
```bash
python main.py --config config/my_groups.json
```

### Dashboard Controls

| Button | Action |
|--------|--------|
| ▶️ Start Monitoring | Begin monitoring all configured groups |
| ⏹️ Stop Monitoring | Stop monitoring |
| 🔄 Sync Excel | Force sync database to Excel |
| 💾 Backup | Create manual Excel backup |
| 📂 Open Excel | Open Excel file in default app |
| Auto Refresh | Toggle automatic dashboard refresh |

---

## 📁 Project Structure

```
whatsapp_moj_automation/
│
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── .gitignore                 # Git ignore rules
│
├── config/
│   ├── __init__.py
│   ├── settings.py            # Centralized configuration
│   └── groups.json            # Group configuration (editable)
│
├── core/
│   ├── __init__.py
│   ├── whatsapp_monitor.py    # Selenium WhatsApp Web monitor
│   ├── message_parser.py      # Regex + AI message parser
│   ├── lawyer_matcher.py    # Lawyer-application mapping
│   └── excel_manager.py       # Excel operations
│
├── database/
│   ├── __init__.py
│   └── db_manager.py          # SQLite database manager
│
├── ui/
│   ├── __init__.py
│   └── dashboard.py           # CustomTkinter dashboard
│
├── utils/
│   ├── __init__.py
│   ├── logger.py              # Logging utilities
│   └── helpers.py             # Common helper functions
│
├── data/                      # Data storage (auto-created)
│   ├── moj_automation.db      # SQLite database
│   ├── moj_transactions.xlsx  # Excel workbook
│   └── processed_ids.json     # Processed message tracking
│
├── logs/                      # Log files (auto-created)
│   └── *.log
│
└── backups/                   # Excel backups (auto-created)
    └── *.xlsx
```

---

## 🔍 Regex Patterns

### Arabic Payment Message
```
يمكنكم دفع رسم طلبكم رقم {NUMBER} من خلال الرابط التالي المخصص لـ: {NAME} {LINK}
```

**Regex:**
```regex
يمكنكم دفع رسم طلبكم رقم\s*(\d+).*?لـ:\s*([^\s].*?)\s+(https?://enotary\.moj\.gov\.ae/[^\s]+)
```

### English Payment Message
```
pay the fee for the Application number : {NUMBER} by the link assigned to : {NAME} {LINK}
```

**Regex:**
```regex
Application number\s*[:\s]\s*(\d+).*?assigned to\s*[:\s]\s*([^\s].*?)\s+(https?://enotary\.moj\.gov\.ae/[^\s]+)
```

### Lawyer Mapping Message
```
681476 انجليزي
```

**Regex:**
```regex
^(\d+)\s+(.+)$
```

---

## 📊 Dashboard Features

### Statistics Cards
- **Today**: Transactions received today
- **Total Gross**: Sum of all gross amounts
- **Commission**: Total broker commissions (20%)
- **Unmatched**: Transactions without lawyer assignment
- **Total**: All-time transaction count
- **Groups**: Number of monitored groups

### Tables
1. **Recent Transactions**: Last 20 transactions with details
2. **By Lawyer**: Aggregated stats per lawyer
3. **By Group**: Aggregated stats per WhatsApp group
4. **Unmatched**: Pending transactions with manual assign buttons
5. **Logs**: Real-time system log viewer

---

## 🔮 Future Upgrades

The project is structured to easily add:

| Feature | Module to Extend |
|---------|-----------------|
| **AI OCR** | `core/message_parser.py` - Add image text extraction |
| **Telegram Integration** | `core/telegram_monitor.py` - New monitor class |
| **ERP Integration** | `core/erp_connector.py` - API connector |
| **PDF Reports** | `core/pdf_generator.py` - Report generator |
| **Real-time Notifications** | `core/notifier.py` - Push/email notifications |
| **Web Dashboard** | `ui/web_dashboard.py` - Flask/FastAPI web UI |

---

## 🛠️ Troubleshooting

### ChromeDriver Issues
```bash
# Update webdriver-manager
pip install --upgrade webdriver-manager

# Or manually download ChromeDriver matching your Chrome version
# from: https://chromedriver.chromium.org/
```

### WhatsApp QR Code Not Appearing
- Make sure Chrome is not running in headless mode for first login
- Delete `./chrome_profile` folder to force fresh login
- Check internet connection

### Arabic Text Display Issues
- Ensure Windows has Arabic language support enabled
- The system uses `pyarabic` and `python-bidi` for proper RTL handling

### Excel File Locked
- Close Excel before running the system
- The system creates backups automatically

### Messages Not Detected
- Verify group names match exactly (case-insensitive)
- Check that WhatsApp Web is fully loaded
- Increase `MESSAGE_POLL_INTERVAL` in `config/settings.py`

---

## 📝 Logging

Logs are stored in `logs/` directory:
- `MainApp.log` - Main application logs
- `WhatsAppMonitor.log` - WhatsApp monitoring logs
- `DatabaseManager.log` - Database operations
- `ExcelManager.log` - Excel operations

Log files rotate at 10MB with 5 backups.

---

## 🔒 Security Notes

- WhatsApp session is stored locally in `./chrome_profile`
- Database and Excel files are stored locally in `./data/`
- No data is sent to external servers
- All processing is done locally on your machine

---

## 📄 License

This project is proprietary software for authorized use only.

---

## 🤝 Support

For issues or questions:
1. Check the logs in `logs/` directory
2. Verify your `config/groups.json` is correct
3. Ensure Chrome and ChromeDriver versions match

---

**Built with Python, Selenium, openpyxl, pandas, and CustomTkinter**
