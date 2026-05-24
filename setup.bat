"""
MOJ E-Notary WhatsApp Automation System
Main Application Entry Point

This is the central orchestrator that connects all components:
- WhatsApp Web monitoring
- Message parsing and extraction
- Lawyer matching
- Database storage
- Excel synchronization
- Dashboard UI
"""
import sys
import os
import json
import signal
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import (
    DATA_DIR, LOGS_DIR, CONFIG_DIR,
    load_groups_config, save_groups_config
)
from database.db_manager import DatabaseManager
from core.whatsapp_monitor import WhatsAppMonitor
from core.message_parser import MessageParser, PaymentData, LawyerMapping
from core.lawyer_matcher import LawyerMatcher
from core.excel_manager import ExcelManager
from ui.dashboard import Dashboard
from utils.logger import setup_logger
from utils.helpers import (
    generate_message_id, is_broker_group,
    load_processed_ids, save_processed_ids
)

logger = setup_logger("MainApp")


class MOJAutomationSystem:
    """
    Main application class that orchestrates all components

    Architecture:
    1. WhatsAppMonitor -> detects new messages
    2. MessageParser -> extracts structured data
    3. LawyerMatcher -> maps lawyers to applications
    4. DatabaseManager -> persists data
    5. ExcelManager -> generates reports
    6. Dashboard -> provides UI
    """

    def __init__(self):
        logger.info("=" * 60)
        logger.info("MOJ E-Notary Automation System Starting...")
        logger.info("=" * 60)

        # Initialize components
        self.db = DatabaseManager()
        self.parser = MessageParser()
        self.lawyer_matcher = LawyerMatcher(self.db)
        self.excel = ExcelManager(self.db)
        self.monitor = WhatsAppMonitor(headless=False)
        self.dashboard: Any = None

        # Configuration
        self.groups_config = load_groups_config()
        self.processed_ids_file = DATA_DIR / "processed_ids.json"
        self.processed_ids: set = load_processed_ids(self.processed_ids_file)

        # State
        self.is_running = False
        self._backup_thread: threading.Thread = None
        self._cleanup_thread: threading.Thread = None

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("System components initialized")

    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.shutdown()
        sys.exit(0)

    def _on_new_messages(self, group_name: str, messages: List[Dict[str, Any]]):
        """
        Callback function triggered when new messages arrive

        Args:
            group_name: Source WhatsApp group
            messages: List of new message dictionaries
        """
        logger.info(f"Processing {len(messages)} new messages from '{group_name}'")

        for msg in messages:
            try:
                msg_id = msg.get("id")
                text = msg.get("text", "")
                sender = msg.get("sender", "Unknown")
                timestamp = msg.get("timestamp", "")

                # Skip if already processed
                if self.db.is_message_processed(msg_id):
                    continue

                # Mark as processed immediately to avoid duplicates
                self.db.mark_message_processed(msg_id, group_name)

                # Determine message type and process accordingly
                if self._is_lawyer_group(group_name):
                    self._process_lawyer_message(msg, group_name)
                elif self._is_payment_group(group_name):
                    self._process_payment_message(msg, group_name)
                else:
                    logger.debug(f"Message from unclassified group: {group_name}")

            except Exception as e:
                logger.error(f"Error processing message: {e}")

    def _is_lawyer_group(self, group_name: str) -> bool:
        """Check if group is the lawyer mapping group"""
        lawyer_group = self.groups_config.get("lawyer_mapping_group", "اعتمادات")
        return lawyer_group.lower() in group_name.lower() or group_name.lower() in lawyer_group.lower()

    def _is_payment_group(self, group_name: str) -> bool:
        """Check if group is a payment group"""
        payment_groups = self.groups_config.get("payment_groups", [])
        return any(pg.lower() in group_name.lower() or group_name.lower() in pg.lower() 
                   for pg in payment_groups)

    def _process_lawyer_message(self, msg: Dict, group_name: str):
        """Process message from lawyer mapping group"""
        text = msg.get("text", "")
        sender = msg.get("sender", "Unknown")

        logger.debug(f"Parsing lawyer message from {sender}")

        result = self.parser.parse_lawyer_message(text, sender)
        if result and result.is_valid:
            # Store mapping
            self.lawyer_matcher.process_lawyer_message(
                app_number=result.app_number,
                lawyer_name=result.lawyer_name,
                group_name=group_name,
                message_text=result.raw_message
            )

            logger.info(f"Lawyer mapping stored: {result.app_number} -> {result.lawyer_name}")

            # Update dashboard log
            if self.dashboard:
                self.dashboard.add_log_message(
                    f"[LAWYER] Mapped: {result.app_number} -> {result.lawyer_name}"
                )

    def _process_payment_message(self, msg: Dict, group_name: str):
        """Process payment message from payment groups"""
        text = msg.get("text", "")
        sender = msg.get("sender", "Unknown")
        timestamp = msg.get("datetime")

        # Quick filter - skip non-payment messages
        if not self.parser.is_payment_message(text):
            logger.debug("Skipping non-payment message")
            return

        logger.debug(f"Parsing payment message")

        result = self.parser.parse_payment_message(text)
        if result and result.is_valid:
            # Check if already in database
            existing = self.db.get_transaction_by_app_number(result.app_number)
            if existing:
                logger.warning(f"Transaction already exists: {result.app_number}")
                return

            # Check if broker group
            broker_groups = self.groups_config.get("broker_groups", [])
            is_broker = is_broker_group(group_name, broker_groups)

            # Get lawyer from mapping (if available)
            lawyer_name = self.lawyer_matcher.get_lawyer_for_app(result.app_number)

            # Prepare transaction data
            transaction_data = {
                "app_number": result.app_number,
                "client_name": result.client_name,
                "lawyer_name": lawyer_name,
                "whatsapp_group": group_name,
                "transaction_type": "e-notary",
                "payment_link": result.payment_link,
                "message_date": timestamp.strftime("%Y-%m-%d %H:%M:%S") if timestamp else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_broker": is_broker,
                "gross_amount": 0.0,  # Will be updated when payment is confirmed
                "commission_percent": self.groups_config.get("commission_percent", 20.0),
                "status": "pending",
                "language": result.language,
                "message_id": msg.get("id"),
                "raw_message": result.raw_message
            }

            # Add to database
            db_success = self.db.add_transaction(transaction_data)

            if db_success:
                # Add to Excel
                excel_success = self.excel.add_transaction(transaction_data)

                status = "✅" if lawyer_name else "⚠️ UNMATCHED"
                logger.info(
                    f"Transaction stored: {result.app_number} | "
                    f"Client: {result.client_name} | "
                    f"Lawyer: {lawyer_name or 'N/A'} | "
                    f"Group: {group_name} {status}"
                )

                # Update dashboard
                if self.dashboard:
                    self.dashboard.add_log_message(
                        f"[PAYMENT] {result.app_number} | {result.client_name[:20]} | "
                        f"Lawyer: {lawyer_name or 'UNMATCHED'}"
                    )
            else:
                logger.warning(f"Failed to store transaction: {result.app_number}")

    def _start_background_tasks(self):
        """Start background maintenance threads"""
        # Daily backup thread
        self._backup_thread = threading.Thread(
            target=self._backup_loop,
            daemon=True,
            name="BackupThread"
        )
        self._backup_thread.start()

        # Cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="CleanupThread"
        )
        self._cleanup_thread.start()

        logger.info("Background tasks started")

    def _backup_loop(self):
        """Run daily Excel backups"""
        last_backup_date = None

        while self.is_running:
            try:
                current_date = datetime.now().date()

                if last_backup_date != current_date:
                    # Time for daily backup
                    backup_time = datetime.now().replace(hour=23, minute=55)
                    if datetime.now() >= backup_time:
                        logger.info("Running daily backup...")
                        self.excel.create_backup()
                        last_backup_date = current_date

                time.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Backup loop error: {e}")
                time.sleep(600)

    def _cleanup_loop(self):
        """Run periodic cleanup tasks"""
        while self.is_running:
            try:
                # Clean old processed messages
                self.db.cleanup_old_processed(days=7)

                # Sleep for 6 hours
                time.sleep(21600)

            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                time.sleep(3600)

    def configure_groups(self, payment_groups: List[str] = None,
                        broker_groups: List[str] = None,
                        internal_groups: List[str] = None,
                        lawyer_group: str = None,
                        commission_percent: float = None):
        """
        Configure WhatsApp groups to monitor

        Args:
            payment_groups: List of payment group names
            broker_groups: List of broker group names
            internal_groups: List of internal group names
            lawyer_group: Lawyer mapping group name
            commission_percent: Default commission percentage
        """
        config = load_groups_config()

        if payment_groups is not None:
            config["payment_groups"] = payment_groups
        if broker_groups is not None:
            config["broker_groups"] = broker_groups
        if internal_groups is not None:
            config["internal_groups"] = internal_groups
        if lawyer_group is not None:
            config["lawyer_mapping_group"] = lawyer_group
        if commission_percent is not None:
            config["commission_percent"] = commission_percent

        save_groups_config(config)
        self.groups_config = config

        # Update monitor
        all_groups = (
            config.get("payment_groups", []) +
            config.get("broker_groups", []) +
            config.get("internal_groups", [])
        )
        # Add lawyer group if not already in list
        lawyer_group_name = config.get("lawyer_mapping_group", "اعتمادات")
        if lawyer_group_name not in all_groups:
            all_groups.append(lawyer_group_name)

        self.monitor.set_monitored_groups(all_groups)

        logger.info(f"Groups configured: {all_groups}")

    def start(self, headless: bool = False, no_ui: bool = False):
        """
        Start the automation system

        Args:
            headless: Run WhatsApp in headless mode (not recommended for first login)
            no_ui: Run without dashboard UI (headless mode)
        """
        logger.info("Starting MOJ Automation System...")

        self.is_running = True

        # Configure monitor
        self.monitor.headless = headless
        self.monitor.add_message_callback(self._on_new_messages)

        # Set monitored groups
        all_groups = (
            self.groups_config.get("payment_groups", []) +
            self.groups_config.get("broker_groups", []) +
            self.groups_config.get("internal_groups", [])
        )
        lawyer_group = self.groups_config.get("lawyer_mapping_group", "اعتمادات")
        if lawyer_group not in all_groups:
            all_groups.append(lawyer_group)

        self.monitor.set_monitored_groups(all_groups)

        # Start background tasks
        self._start_background_tasks()

        if no_ui:
            # Headless mode - just monitor
            logger.info("Running in headless mode (no UI)")
            success = self.monitor.start_monitoring()
            if success:
                logger.info("Monitoring started in headless mode")
                try:
                    while self.is_running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt received")
            else:
                logger.error("Failed to start monitoring")
        else:
            # UI mode
            logger.info("Starting dashboard UI...")
            self.dashboard = Dashboard(self.db, self.monitor, self.excel)

            # Start monitoring in background
            def start_monitor_bg():
                time.sleep(2)  # Let UI load first
                success = self.monitor.start_monitoring()
                if success:
                    self.dashboard.add_log_message("✅ Monitoring started successfully")
                else:
                    self.dashboard.add_log_message("❌ Failed to start monitoring")

            threading.Thread(target=start_monitor_bg, daemon=True).start()

            # Run dashboard
            self.dashboard.run()

    def shutdown(self):
        """Gracefully shutdown the system"""
        logger.info("Shutting down system...")
        self.is_running = False

        # Stop monitor
        self.monitor.disconnect()

        # Create final backup
        try:
            self.excel.create_backup()
        except Exception as e:
            logger.error(f"Final backup error: {e}")

        # Save processed IDs
        try:
            save_processed_ids(self.processed_ids_file, self.processed_ids)
        except Exception as e:
            logger.error(f"Save processed IDs error: {e}")

        logger.info("System shutdown complete")

    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "running": self.is_running,
            "monitor_status": self.monitor.get_connection_status(),
            "database_stats": self.db.get_dashboard_stats(),
            "excel_path": str(self.excel.get_excel_path()),
            "groups_config": self.groups_config
        }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="MOJ E-Notary WhatsApp Automation System"
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Run WhatsApp in headless mode"
    )
    parser.add_argument(
        "--no-ui", action="store_true",
        help="Run without dashboard UI"
    )
    parser.add_argument(
        "--config", type=str,
        help="Path to groups configuration JSON file"
    )

    args = parser.parse_args()

    # Create system instance
    system = MOJAutomationSystem()

    # Load custom config if provided
    if args.config:
        try:
            with open(args.config, "r", encoding="utf-8") as f:
                config = json.load(f)
                system.configure_groups(
                    payment_groups=config.get("payment_groups"),
                    broker_groups=config.get("broker_groups"),
                    internal_groups=config.get("internal_groups"),
                    lawyer_group=config.get("lawyer_mapping_group"),
                    commission_percent=config.get("commission_percent")
                )
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            print(f"Error loading config file: {e}")
            return

    try:
        system.start(headless=args.headless, no_ui=args.no_ui)
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        print(f"Fatal error: {e}")
    finally:
        system.shutdown()


if __name__ == "__main__":
    main()
