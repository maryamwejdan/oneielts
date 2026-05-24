"""
Dashboard UI Module
Desktop dashboard using CustomTkinter
Displays real-time statistics and system status
"""
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
import customtkinter as ctk
from tkinter import messagebox, filedialog
from config.settings import (
    DASHBOARD_TITLE, DASHBOARD_WIDTH, DASHBOARD_HEIGHT,
    THEME, COLOR_THEME
)
from database.db_manager import DatabaseManager
from core.whatsapp_monitor import WhatsAppMonitor
from core.excel_manager import ExcelManager
from utils.logger import setup_logger
from utils.helpers import format_currency

logger = setup_logger("Dashboard")


class Dashboard:
    """
    Main dashboard window for the MOJ Automation System
    Features:
    - Real-time statistics display
    - Connection status
    - Transaction tables
    - Control buttons
    - Auto-refresh
    """

    def __init__(self, db_manager: DatabaseManager, 
                 whatsapp_monitor: WhatsAppMonitor,
                 excel_manager: ExcelManager):
        self.db = db_manager
        self.monitor = whatsapp_monitor
        self.excel = excel_manager

        # Setup theme
        ctk.set_appearance_mode(THEME)
        ctk.set_default_color_theme(COLOR_THEME)

        # Main window
        self.root = ctk.CTk()
        self.root.title(DASHBOARD_TITLE)
        self.root.geometry(f"{DASHBOARD_WIDTH}x{DASHBOARD_HEIGHT}")
        self.root.minsize(1200, 700)

        # State
        self.is_monitoring = False
        self.auto_refresh = True
        self.refresh_interval = 5000  # ms

        self._build_ui()
        self._start_refresh_loop()

        logger.info("Dashboard initialized")

    def _build_ui(self):
        """Build the complete UI layout"""
        # Main grid layout
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        # Header
        self._build_header()

        # Main content area
        self.content_frame = ctk.CTkFrame(self.root)
        self.content_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Left panel - Stats
        self._build_stats_panel()

        # Right panel - Tables
        self._build_tables_panel()

        # Bottom panel - Controls
        self._build_control_panel()

    def _build_header(self):
        """Build header with title and status"""
        header = ctk.CTkFrame(self.root, height=60)
        header.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        header.grid_propagate(False)

        # Title
        title = ctk.CTkLabel(
            header, 
            text="🏛️ MOJ E-Notary Automation System",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.place(relx=0.02, rely=0.5, anchor="w")

        # Status indicator
        self.status_label = ctk.CTkLabel(
            header,
            text="⚫ Disconnected",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        self.status_label.place(relx=0.98, rely=0.5, anchor="e")

    def _build_stats_panel(self):
        """Build statistics cards panel"""
        stats_frame = ctk.CTkFrame(self.content_frame)
        stats_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Title
        ctk.CTkLabel(
            stats_frame,
            text="📊 Real-Time Statistics",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(10, 5))

        # Stats grid
        stats_grid = ctk.CTkFrame(stats_frame)
        stats_grid.pack(padx=10, pady=5, fill="both", expand=True)

        # Card 1: Today's Transactions
        self.card_today = self._create_stat_card(
            stats_grid, "Today", "0", "transactions", 0, 0, "#2E7D32"
        )

        # Card 2: Total Gross
        self.card_gross = self._create_stat_card(
            stats_grid, "Total Gross", "0.00", "AED", 0, 1, "#1565C0"
        )

        # Card 3: Total Commission
        self.card_commission = self._create_stat_card(
            stats_grid, "Commission", "0.00", "AED", 0, 2, "#C62828"
        )

        # Card 4: Unmatched
        self.card_unmatched = self._create_stat_card(
            stats_grid, "Unmatched", "0", "pending", 1, 0, "#F57C00"
        )

        # Card 5: Total All Time
        self.card_total = self._create_stat_card(
            stats_grid, "Total", "0", "transactions", 1, 1, "#6A1B9A"
        )

        # Card 6: Active Groups
        self.card_groups = self._create_stat_card(
            stats_grid, "Groups", "0", "monitored", 1, 2, "#00695C"
        )

    def _create_stat_card(self, parent, title, value, unit, row, col, color):
        """Create a single statistics card"""
        card = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"))
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(
            card, text=title,
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=(10, 0))

        value_label = ctk.CTkLabel(
            card, text=value,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=color
        )
        value_label.pack(pady=(0, 0))

        ctk.CTkLabel(
            card, text=unit,
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(pady=(0, 10))

        return value_label

    def _build_tables_panel(self):
        """Build tables panel with tabs"""
        tables_frame = ctk.CTkFrame(self.content_frame)
        tables_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        tables_frame.grid_columnconfigure(0, weight=1)
        tables_frame.grid_rowconfigure(0, weight=1)

        # Tab view
        self.tab_view = ctk.CTkTabview(tables_frame)
        self.tab_view.pack(padx=10, pady=10, fill="both", expand=True)

        # Tabs
        self.tab_view.add("Recent Transactions")
        self.tab_view.add("By Lawyer")
        self.tab_view.add("By Group")
        self.tab_view.add("Unmatched")
        self.tab_view.add("Logs")

        # Recent Transactions tab
        self._build_transactions_tab()

        # By Lawyer tab
        self._build_lawyer_tab()

        # By Group tab
        self._build_group_tab()

        # Unmatched tab
        self._build_unmatched_tab()

        # Logs tab
        self._build_logs_tab()

    def _build_transactions_tab(self):
        """Build recent transactions table"""
        tab = self.tab_view.tab("Recent Transactions")

        # Scrollable frame
        scroll = ctk.CTkScrollableFrame(tab)
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Headers
        headers = ["App #", "Client", "Lawyer", "Group", "Amount", "Status", "Date"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(
                scroll, text=h,
                font=ctk.CTkFont(weight="bold", size=12),
                width=120 if i < 3 else 100
            ).grid(row=0, column=i, padx=3, pady=3, sticky="w")

        self.transactions_rows = []

    def _build_lawyer_tab(self):
        """Build lawyer statistics tab"""
        tab = self.tab_view.tab("By Lawyer")
        scroll = ctk.CTkScrollableFrame(tab)
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        headers = ["Lawyer Name", "Count", "Total Gross", "Total Commission"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(
                scroll, text=h,
                font=ctk.CTkFont(weight="bold", size=12),
                width=150
            ).grid(row=0, column=i, padx=5, pady=3, sticky="w")

        self.lawyer_rows = []

    def _build_group_tab(self):
        """Build group statistics tab"""
        tab = self.tab_view.tab("By Group")
        scroll = ctk.CTkScrollableFrame(tab)
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        headers = ["Group Name", "Count", "Total Gross"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(
                scroll, text=h,
                font=ctk.CTkFont(weight="bold", size=12),
                width=200
            ).grid(row=0, column=i, padx=5, pady=3, sticky="w")

        self.group_rows = []

    def _build_unmatched_tab(self):
        """Build unmatched transactions tab"""
        tab = self.tab_view.tab("Unmatched")
        scroll = ctk.CTkScrollableFrame(tab)
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        headers = ["App #", "Client", "Group", "Date", "Actions"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(
                scroll, text=h,
                font=ctk.CTkFont(weight="bold", size=12),
                width=140
            ).grid(row=0, column=i, padx=5, pady=3, sticky="w")

        self.unmatched_rows = []

    def _build_logs_tab(self):
        """Build system logs tab"""
        tab = self.tab_view.tab("Logs")

        self.log_text = ctk.CTkTextbox(tab, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text.configure(state="disabled")

    def _build_control_panel(self):
        """Build bottom control panel"""
        controls = ctk.CTkFrame(self.root, height=60)
        controls.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="ew")
        controls.grid_propagate(False)

        # Start/Stop button
        self.btn_toggle = ctk.CTkButton(
            controls,
            text="▶️ Start Monitoring",
            command=self._toggle_monitoring,
            width=180,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.btn_toggle.place(relx=0.02, rely=0.5, anchor="w")

        # Sync Excel button
        self.btn_sync = ctk.CTkButton(
            controls,
            text="🔄 Sync Excel",
            command=self._sync_excel,
            width=140,
            height=35
        )
        self.btn_sync.place(relx=0.18, rely=0.5, anchor="w")

        # Backup button
        self.btn_backup = ctk.CTkButton(
            controls,
            text="💾 Backup",
            command=self._create_backup,
            width=120,
            height=35
        )
        self.btn_backup.place(relx=0.32, rely=0.5, anchor="w")

        # Open Excel button
        self.btn_open = ctk.CTkButton(
            controls,
            text="📂 Open Excel",
            command=self._open_excel,
            width=120,
            height=35
        )
        self.btn_open.place(relx=0.44, rely=0.5, anchor="w")

        # Auto-refresh toggle
        self.chk_auto = ctk.CTkCheckBox(
            controls,
            text="Auto Refresh",
            command=self._toggle_auto_refresh,
            onvalue=True,
            offvalue=False
        )
        self.chk_auto.place(relx=0.58, rely=0.5, anchor="w")
        self.chk_auto.select()

        # Last update label
        self.lbl_last_update = ctk.CTkLabel(
            controls,
            text="Last update: Never",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.lbl_last_update.place(relx=0.98, rely=0.5, anchor="e")

    def _toggle_monitoring(self):
        """Start or stop monitoring"""
        if not self.is_monitoring:
            # Start
            self.btn_toggle.configure(
                text="⏹️ Stop Monitoring",
                fg_color=("#C62828", "#C62828"),
                hover_color=("#B71C1C", "#B71C1C")
            )
            self.is_monitoring = True

            # Start in thread to avoid blocking UI
            threading.Thread(target=self._start_monitor, daemon=True).start()

        else:
            # Stop
            self.btn_toggle.configure(
                text="▶️ Start Monitoring",
                fg_color=("#1F6AA5", "#1F6AA5"),
                hover_color=("#144870", "#144870")
            )
            self.is_monitoring = False
            self.monitor.stop_monitoring()

    def _start_monitor(self):
        """Start monitoring in background"""
        try:
            success = self.monitor.start_monitoring()
            if not success:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", "Failed to start monitoring. Check logs for details."
                ))
                self.is_monitoring = False
                self.root.after(0, self._update_toggle_button_stop)
        except Exception as e:
            logger.error(f"Start monitor error: {e}")
            self.is_monitoring = False
            self.root.after(0, self._update_toggle_button_stop)

    def _update_toggle_button_stop(self):
        """Update toggle button to stopped state"""
        self.btn_toggle.configure(
            text="▶️ Start Monitoring",
            fg_color=("#1F6AA5", "#1F6AA5"),
            hover_color=("#144870", "#144870")
        )

    def _sync_excel(self):
        """Sync database to Excel"""
        try:
            count = self.excel.sync_from_database()
            messagebox.showinfo("Sync Complete", f"Synced {count} transactions to Excel")
            self._refresh_data()
        except Exception as e:
            messagebox.showerror("Error", f"Sync failed: {e}")

    def _create_backup(self):
        """Create Excel backup"""
        try:
            path = self.excel.create_backup()
            if path:
                messagebox.showinfo("Backup Created", f"Saved to:
{path}")
            else:
                messagebox.showwarning("Warning", "No Excel file to backup")
        except Exception as e:
            messagebox.showerror("Error", f"Backup failed: {e}")

    def _open_excel(self):
        """Open Excel file in default application"""
        try:
            import os
            path = str(self.excel.get_excel_path())
            if os.path.exists(path):
                os.startfile(path)
            else:
                messagebox.showwarning("Warning", "Excel file not found")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open Excel: {e}")

    def _toggle_auto_refresh(self):
        """Toggle auto-refresh"""
        self.auto_refresh = self.chk_auto.get()

    def _start_refresh_loop(self):
        """Start auto-refresh loop"""
        self._refresh_data()
        self._schedule_refresh()

    def _schedule_refresh(self):
        """Schedule next refresh"""
        if self.auto_refresh:
            self.root.after(self.refresh_interval, self._refresh_cycle)

    def _refresh_cycle(self):
        """Refresh cycle callback"""
        if self.auto_refresh:
            self._refresh_data()
            self._schedule_refresh()

    def _refresh_data(self):
        """Refresh all dashboard data"""
        try:
            # Update stats
            stats = self.db.get_dashboard_stats()

            self.card_today.configure(text=str(stats["today_count"]))
            self.card_gross.configure(text=f"{stats['total_gross']:,.2f}")
            self.card_commission.configure(text=f"{stats['total_commission']:,.2f}")
            self.card_unmatched.configure(text=str(stats["unmatched_count"]))
            self.card_total.configure(text=str(stats["total_count"]))
            self.card_groups.configure(text=str(len(stats["group_stats"])))

            # Update connection status
            status = self.monitor.get_connection_status()
            if status["connected"]:
                self.status_label.configure(
                    text="🟢 Connected",
                    text_color="#2E7D32"
                )
            elif self.is_monitoring:
                self.status_label.configure(
                    text="🟡 Connecting...",
                    text_color="#F57C00"
                )
            else:
                self.status_label.configure(
                    text="⚫ Disconnected",
                    text_color="gray"
                )

            # Update tables
            self._update_transactions_table()
            self._update_lawyer_table(stats["lawyer_stats"])
            self._update_group_table(stats["group_stats"])
            self._update_unmatched_table()

            # Update timestamp
            self.lbl_last_update.configure(
                text=f"Last update: {datetime.now().strftime('%H:%M:%S')}"
            )

        except Exception as e:
            logger.error(f"Refresh error: {e}")

    def _update_transactions_table(self):
        """Update recent transactions table"""
        try:
            transactions = self.db.get_all_transactions(limit=50)

            # Clear existing rows
            for widget in self.tab_view.tab("Recent Transactions").winfo_children()[0].winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    widget.destroy()

            scroll = self.tab_view.tab("Recent Transactions").winfo_children()[0]

            for i, t in enumerate(transactions[:20], start=1):
                values = [
                    t.get("app_number", ""),
                    t.get("client_name", "")[:20],
                    t.get("lawyer_name", "")[:15] or "-",
                    t.get("whatsapp_group", "")[:15],
                    f"{t.get('gross_amount', 0):,.0f}",
                    t.get("status", ""),
                    str(t.get("message_date", ""))[:10]
                ]

                for j, val in enumerate(values):
                    ctk.CTkLabel(
                        scroll, text=str(val),
                        font=ctk.CTkFont(size=11),
                        width=120 if j < 3 else 100
                    ).grid(row=i, column=j, padx=3, pady=2, sticky="w")

        except Exception as e:
            logger.error(f"Update transactions table error: {e}")

    def _update_lawyer_table(self, lawyer_stats: list):
        """Update lawyer statistics table"""
        try:
            scroll = self.tab_view.tab("By Lawyer").winfo_children()[0]

            # Clear old rows (keep header row 0)
            for widget in scroll.winfo_children():
                info = widget.grid_info()
                if info.get("row", 0) > 0:
                    widget.destroy()

            for i, stat in enumerate(lawyer_stats, start=1):
                values = [
                    stat.get("lawyer_name", ""),
                    str(stat.get("count", 0)),
                    f"{stat.get('total', 0):,.2f}",
                    f"{stat.get('total', 0) * 0.2:,.2f}"
                ]

                for j, val in enumerate(values):
                    ctk.CTkLabel(
                        scroll, text=str(val),
                        font=ctk.CTkFont(size=11),
                        width=150
                    ).grid(row=i, column=j, padx=5, pady=2, sticky="w")

        except Exception as e:
            logger.error(f"Update lawyer table error: {e}")

    def _update_group_table(self, group_stats: list):
        """Update group statistics table"""
        try:
            scroll = self.tab_view.tab("By Group").winfo_children()[0]

            for widget in scroll.winfo_children():
                info = widget.grid_info()
                if info.get("row", 0) > 0:
                    widget.destroy()

            for i, stat in enumerate(group_stats, start=1):
                values = [
                    stat.get("whatsapp_group", ""),
                    str(stat.get("count", 0)),
                    f"{stat.get('total', 0):,.2f}"
                ]

                for j, val in enumerate(values):
                    ctk.CTkLabel(
                        scroll, text=str(val),
                        font=ctk.CTkFont(size=11),
                        width=200
                    ).grid(row=i, column=j, padx=5, pady=2, sticky="w")

        except Exception as e:
            logger.error(f"Update group table error: {e}")

    def _update_unmatched_table(self):
        """Update unmatched transactions table"""
        try:
            unmatched = self.db.get_unmatched_transactions()
            scroll = self.tab_view.tab("Unmatched").winfo_children()[0]

            for widget in scroll.winfo_children():
                info = widget.grid_info()
                if info.get("row", 0) > 0:
                    widget.destroy()

            for i, t in enumerate(unmatched[:20], start=1):
                values = [
                    t.get("app_number", ""),
                    t.get("client_name", "")[:20],
                    t.get("whatsapp_group", "")[:15],
                    str(t.get("message_date", ""))[:10]
                ]

                for j, val in enumerate(values):
                    ctk.CTkLabel(
                        scroll, text=str(val),
                        font=ctk.CTkFont(size=11),
                        width=140
                    ).grid(row=i, column=j, padx=5, pady=2, sticky="w")

                # Add assign button
                ctk.CTkButton(
                    scroll, text="Assign",
                    width=80, height=20,
                    font=ctk.CTkFont(size=10),
                    command=lambda app=t.get("app_number"): self._manual_assign(app)
                ).grid(row=i, column=4, padx=5, pady=2)

        except Exception as e:
            logger.error(f"Update unmatched table error: {e}")

    def _manual_assign(self, app_number: str):
        """Manually assign lawyer to unmatched transaction"""
        # Simple dialog - in production, use a proper dialog
        from tkinter import simpledialog
        lawyer = simpledialog.askstring("Assign Lawyer", f"Enter lawyer name for {app_number}:")
        if lawyer:
            self.db.add_lawyer_mapping(app_number, lawyer)
            self._refresh_data()

    def add_log_message(self, message: str):
        """Add message to logs tab"""
        try:
            self.log_text.configure(state="normal")
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert("end", f"[{timestamp}] {message}
")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        except Exception:
            pass

    def run(self):
        """Start the dashboard main loop"""
        self.root.mainloop()

    def stop(self):
        """Stop dashboard and cleanup"""
        self.auto_refresh = False
        if self.is_monitoring:
            self.monitor.stop_monitoring()
        self.root.destroy()
