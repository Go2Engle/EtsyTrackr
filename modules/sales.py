from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTableWidget, QTableWidgetItem,
                           QHeaderView, QComboBox, QFileDialog, QMessageBox, QCheckBox, QMenu, QApplication)
from PySide6.QtCore import Qt, QDate, QUrl, QTimer, Signal
from PySide6.QtGui import QDesktopServices, QBrush, QColor, QIcon
import pandas as pd
import os
import re
import shutil
from datetime import datetime, timedelta
import calendar

class SalesWidget(QWidget):
    data_changed = Signal()  # Add signal for data changes
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.app_icon = QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icon.png'))
        self.init_ui()
        
        # Create a timer for auto-refresh (every 5 minutes)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_table)
        self.refresh_timer.start(300000)  # 300000 ms = 5 minutes

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Controls bar
        controls_layout = QHBoxLayout()
        
        # Left side - Statement controls
        left_controls = QVBoxLayout()
        
        etsy_link = QPushButton("Go to Etsy Monthly Statement")
        etsy_link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.etsy.com/your/account/payments/monthly-statement")))
        
        instructions = QLabel("1. Click the link above to go to Etsy\n2. Choose month and year\n3. Generate and download the CSV\n4. Import it below")
        instructions.setStyleSheet("color: #666; margin: 10px;")
        
        left_controls.addWidget(etsy_link)
        left_controls.addWidget(instructions)
        
        controls_layout.addLayout(left_controls)
        controls_layout.addStretch()
        
        # Right side - Import and Clear controls
        right_controls = QHBoxLayout()
        
        import_btn = QPushButton("Import Statement")
        import_btn.clicked.connect(self.import_statement)
        right_controls.addWidget(import_btn)
        
        self.scan_downloads = QCheckBox("Scan Downloads Folder")
        self.scan_downloads.setToolTip("Automatically scan Downloads folder for new Etsy statement files")
        right_controls.addWidget(self.scan_downloads)
        
        clear_btn = QPushButton("Clear Sales Data")
        clear_btn.clicked.connect(self.clear_sales_data)
        clear_btn.setStyleSheet("QPushButton { color: red; }")
        right_controls.addWidget(clear_btn)
        
        controls_layout.addLayout(right_controls)
        
        layout.addLayout(controls_layout)
        
        # Add date filter controls
        filter_layout = QHBoxLayout()
        
        self.date_filter = QComboBox()
        self.date_filter.addItems(['All Time', 'This Year', 'Last 30 Days', 'This Month', 'Last Month'])
        self.date_filter.currentTextChanged.connect(self.refresh_table)
        
        self.year_filter = QComboBox()
        self.year_filter.addItems(['All Years'] + [str(year) for year in range(2024, 2030)])
        self.year_filter.currentTextChanged.connect(self.refresh_table)
        
        self.month_filter = QComboBox()
        self.month_filter.addItems(['All Months'] + [calendar.month_name[i] for i in range(1, 13)])
        self.month_filter.currentTextChanged.connect(self.refresh_table)
        
        filter_layout.addWidget(QLabel('View:'))
        filter_layout.addWidget(self.date_filter)
        filter_layout.addWidget(self.year_filter)
        filter_layout.addWidget(self.month_filter)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Sales table
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            'Date', 'Order ID', 'Items', 'Sale Amount', 'Shipping Fee',
            'Sales Tax', 'Ship Trans Fee', 'Item Trans Fee', 'Processing Fee',
            'Listing Fee', 'Net'
        ])
        
        # Set table properties
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        
        # Set column widths and resize modes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Items column stretches
        
        # Fixed widths for other columns
        fixed_widths = {
            0: 100,  # Date
            1: 100,  # Order ID
            3: 100,  # Sale Amount
            4: 100,  # Shipping Fee
            5: 100,  # Sales Tax
            6: 100,  # Ship Trans Fee
            7: 100,  # Item Trans Fee
            8: 100,  # Processing Fee
            9: 100,  # Listing Fee
            10: 100  # Net
        }
        
        for col, width in fixed_widths.items():
            self.table.setColumnWidth(col, width)
            header.setSectionResizeMode(col, QHeaderView.Fixed)
        
        # Enable context menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.table)
        
        # Status label at the bottom
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Initial refresh
        self.refresh_table()
    
    def clean_amount(self, amount_str):
        """Convert currency string to float"""
        if isinstance(amount_str, float):
            return amount_str
        if pd.isna(amount_str) or amount_str == '--':
            return 0.0
        # Remove $ and any spaces, then convert to float
        return float(str(amount_str).replace('$', '').replace(',', '').strip())
    
    def extract_order_id(self, info):
        """Extract order ID from Info field"""
        if pd.isna(info):
            return 'Unknown'
        info = str(info)
        try:
            return info.split('Order #')[1].split()[0] if 'Order #' in info else info
        except:
            return 'Unknown'
    
    def _date_in_filter(self, date):
        """Check if date is within selected period"""
        period_filter = self.period_combo.currentText()
        
        if period_filter == "All Time":
            return True
        elif period_filter == "This Month":
            return date.year == datetime.now().year and date.month == datetime.now().month
        elif period_filter == "Last Month":
            last_month = datetime.now() - pd.DateOffset(months=1)
            return date.year == last_month.year and date.month == last_month.month
        elif period_filter == "This Year":
            return date.year == datetime.now().year
        elif period_filter == "Last Year":
            return date.year == datetime.now().year - 1
        
        return False
    
    def get_date_filter(self):
        """Get the date filter based on current selections"""
        filter_type = self.date_filter.currentText()
        selected_year = self.year_filter.currentText()
        selected_month = self.month_filter.currentText()
        
        now = datetime.now()
        
        if filter_type == 'Last 30 Days':
            return now - timedelta(days=30), now
        elif filter_type == 'This Month':
            return datetime(now.year, now.month, 1), now
        elif filter_type == 'Last Month':
            first_day = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
            last_day = now.replace(day=1) - timedelta(days=1)
            return first_day, last_day
        elif filter_type == 'This Year':
            return datetime(now.year, 1, 1), now
        elif selected_year != 'All Years':
            year = int(selected_year)
            if selected_month != 'All Months':
                month = list(calendar.month_name).index(selected_month)
                next_month = month + 1 if month < 12 else 1
                next_year = year if month < 12 else year + 1
                return datetime(year, month, 1), datetime(next_year, next_month, 1) - timedelta(days=1)
            return datetime(year, 1, 1), datetime(year + 1, 1, 1) - timedelta(days=1)
        
        return None, None  # No date filter
    
    def get_filtered_data(self):
        """Get the filtered data based on current selections"""
        start_date, end_date = self.get_date_filter()
        
        # Process each statement file
        data = []
        for filename in os.listdir(self.db.statements_dir):
            if not filename.endswith('.csv'):
                continue
                
            file_path = os.path.join(self.db.statements_dir, filename)
            try:
                df = pd.read_csv(file_path)
                
                # Process the data
                processed_df = self.db.process_statement_data(df)
                if processed_df is None:
                    continue
                
                for _, row in processed_df.iterrows():
                    sale_date = row['Date']
                    
                    # Apply date filter if set
                    if start_date and end_date:
                        if not (start_date <= sale_date <= end_date):
                            continue
                    
                    data.append({
                        'Date': sale_date,
                        'Order ID': row['Order ID'],
                        'Items': row['Items'],
                        'Sale Amount': row['Sale Amount'],
                        'Shipping Fee': row['Shipping Fee'],
                        'Sales Tax': row['Sales Tax'],
                        'Shipping Transaction Fee': row['Shipping Transaction Fee'],
                        'Item Transaction Fee': row['Item Transaction Fee'],
                        'Processing Fee': row['Processing Fee'],
                        'Listing Fee': row['Listing Fee'],
                        'Net': row['Net']
                    })
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
        
        if not data:
            return None
        
        return pd.DataFrame(data)
    
    def refresh_table(self):
        """Refresh the sales table with current data"""
        try:
            # Get filtered data
            df = self.get_filtered_data()
            if df is None or df.empty:
                self.table.setRowCount(0)
                self.status_label.setText("No data available")
                return
            
            # Update table
            self.table.setRowCount(len(df))
            
            # Initialize totals
            total_sales = 0
            total_shipping = 0
            total_transaction_fees = 0
            total_listing_fees = 0
            total_processing_fees = 0
            total_tax = 0
            total_refunds = 0
            
            # Format and display data
            for i, row in df.iterrows():
                # Date
                date_item = QTableWidgetItem(row['Date'].strftime('%Y-%m-%d'))
                self.table.setItem(i, 0, date_item)
                
                # Order ID
                order_item = QTableWidgetItem(str(row['Order ID']))
                self.table.setItem(i, 1, order_item)
                
                # Items
                items_item = QTableWidgetItem(str(row['Items']))
                self.table.setItem(i, 2, items_item)
                
                # Financial columns with right alignment
                financial_cols = [
                    ('Sale Amount', 3),
                    ('Shipping Fee', 4),
                    ('Sales Tax', 5),
                    ('Shipping Transaction Fee', 6),
                    ('Item Transaction Fee', 7),
                    ('Processing Fee', 8),
                    ('Listing Fee', 9)
                ]
                
                # Calculate row net
                row_net = float(row.get('Sale Amount', 0) or 0)
                row_net += float(row.get('Shipping Fee', 0) or 0)
                row_net += float(row.get('Sales Tax', 0) or 0)
                row_net += float(row.get('Shipping Transaction Fee', 0) or 0)
                row_net += float(row.get('Item Transaction Fee', 0) or 0)
                row_net += float(row.get('Processing Fee', 0) or 0)
                row_net += float(row.get('Listing Fee', 0) or 0)
                
                # Display financial columns
                for col_name, col_idx in financial_cols:
                    amount = row.get(col_name, 0)
                    if pd.isna(amount):
                        amount = 0
                    amount = float(amount)
                    
                    item = QTableWidgetItem(f"${amount:.2f}")
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    
                    if amount < 0:
                        item.setForeground(QBrush(QColor('red')))
                    
                    self.table.setItem(i, col_idx, item)
                    
                    # Update running totals
                    if col_name == 'Sale Amount':
                        if '[REFUNDED]' in str(row['Items']):
                            item.setForeground(QBrush(QColor('red')))
                            total_refunds -= amount
                        if amount > 0:
                            total_sales += amount
                    elif col_name == 'Shipping Fee':
                        if 'Label #' in str(row['Order ID']):
                            item.setForeground(QBrush(QColor('red')))
                        total_shipping += amount
                    elif col_name == 'Sales Tax':
                        total_tax += amount
                    elif col_name == 'Shipping Transaction Fee' or col_name == 'Item Transaction Fee':
                        total_transaction_fees += amount
                    elif col_name == 'Processing Fee':
                        total_processing_fees += amount
                    elif col_name == 'Listing Fee':
                        total_listing_fees += amount
                
                # Add Net column
                net_item = QTableWidgetItem(f"${row_net:.2f}")
                net_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if row_net < 0:
                    net_item.setForeground(QBrush(QColor('red')))
                self.table.setItem(i, 10, net_item)
            
            # Calculate net profit
            net_profit = (total_sales + 
                           total_shipping +
                           total_transaction_fees + 
                           total_listing_fees + 
                           total_processing_fees +
                           total_tax +
                           total_refunds)  # Refunds are now properly negative
            
            # Create status text with all totals
            status_parts = [
                f"Sales: ${total_sales:,.2f}",
                f"Shipping: ${total_shipping:,.2f}",
                f"Transaction Fees: ${total_transaction_fees:,.2f}",
                f"Listing Fees: ${total_listing_fees:,.2f}",
                f"Processing Fees: ${total_processing_fees:,.2f}",
                f"Tax: ${total_tax:,.2f}",
                f"Refunds: ${total_refunds:,.2f}",  # Already negative
                f"Net Profit: ${net_profit:,.2f}"
            ]
            
            # Join with dividers and set status
            self.status_label.setText(" | ".join(status_parts))
            
            # Emit signal after data is refreshed
            self.data_changed.emit()
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error refreshing table: {str(e)}')
    
    def import_statement(self):
        try:
            scan_downloads = self.scan_downloads.isChecked()
            
            if scan_downloads:
                # Get user's downloads folder
                downloads_path = os.path.expanduser("~/Downloads")
                
                # Look for Etsy statement files and group by year/month
                statement_files_by_month = {}
                for filename in os.listdir(downloads_path):
                    match = re.match(r'etsy_statement_(\d{4})_(\d{1,2})(?:[ ]*\(\d+\))?.csv', filename, re.IGNORECASE)
                    if match:
                        file_path = os.path.join(downloads_path, filename)
                        year, month = match.groups()
                        key = f"{year}_{month.zfill(2)}"
                        
                        # Add to dictionary, keeping track of modification time
                        if key not in statement_files_by_month or \
                           os.path.getmtime(file_path) > os.path.getmtime(statement_files_by_month[key]):
                            statement_files_by_month[key] = file_path
                
                if statement_files_by_month:
                    # Ask user if they want to import the found files
                    msg = QMessageBox()
                    msg.setWindowIcon(self.app_icon)
                    msg.setWindowTitle("Import Statements")
                    msg.setIcon(QMessageBox.Information)
                    msg.setText(f"Found statement files for {len(statement_files_by_month)} month(s) in Downloads folder.")
                    msg.setInformativeText("Would you like to import them? This will replace any existing statements for these months.")
                    msg.setDetailedText("Latest files found:\n" + "\n".join(os.path.basename(f) for f in statement_files_by_month.values()))
                    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    
                    if msg.exec_() == QMessageBox.Yes:
                        # For each month's statement
                        for year_month, file_path in statement_files_by_month.items():
                            # Remove any existing statements for this month
                            for existing_file in os.listdir(self.db.statements_dir):
                                if existing_file.startswith(f"etsy_statement_{year_month}"):
                                    os.remove(os.path.join(self.db.statements_dir, existing_file))
                            
                            # Copy the new statement
                            base_name = f"etsy_statement_{year_month}.csv"
                            dest_path = os.path.join(self.db.statements_dir, base_name)
                            shutil.copy2(file_path, dest_path)
                        
                        self.refresh_table()
                        return
                    
                else:
                    QMessageBox.information(self, "No Files Found", 
                                         "No Etsy statement files found in Downloads folder.")
            
            # If not scanning downloads or no files found, show file dialog
            file_dialog = QFileDialog()
            file_paths, _ = file_dialog.getOpenFileNames(
                self,
                "Select Etsy Statement(s)",
                os.path.expanduser("~/Downloads"),
                "CSV Files (*.csv)"
            )
            
            if file_paths:
                # Group selected files by month
                selected_files_by_month = {}
                for file_path in file_paths:
                    filename = os.path.basename(file_path)
                    match = re.match(r'etsy_statement_(\d{4})_(\d{1,2})(?:[ ]*\(\d+\))?.csv', filename, re.IGNORECASE)
                    if match:
                        year, month = match.groups()
                        key = f"{year}_{month.zfill(2)}"
                        
                        # Add to dictionary, keeping track of modification time
                        if key not in selected_files_by_month or \
                           os.path.getmtime(file_path) > os.path.getmtime(selected_files_by_month[key]):
                            selected_files_by_month[key] = file_path
                
                # Import each month's latest statement
                for year_month, file_path in selected_files_by_month.items():
                    # Remove any existing statements for this month
                    for existing_file in os.listdir(self.db.statements_dir):
                        if existing_file.startswith(f"etsy_statement_{year_month}"):
                            os.remove(os.path.join(self.db.statements_dir, existing_file))
                    
                    # Copy the new statement
                    base_name = f"etsy_statement_{year_month}.csv"
                    dest_path = os.path.join(self.db.statements_dir, base_name)
                    shutil.copy2(file_path, dest_path)
                
                self.refresh_table()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import statement: {str(e)}")

    def clear_sales_data(self):
        """Clear all sales data after confirmation"""
        reply = QMessageBox.question(
            self,
            'Clear Sales Data',
            'Are you sure you want to clear all sales data? This cannot be undone.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Clear the statements directory
                for filename in os.listdir(self.db.statements_dir):
                    if filename.endswith('.csv'):
                        os.remove(os.path.join(self.db.statements_dir, filename))
                
                # Clear the table
                self.table.setRowCount(0)
                
                # Clear the status label
                self.status_label.setText("")
                
                QMessageBox.information(
                    self,
                    'Success',
                    'All sales data has been cleared.'
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    'Error',
                    f'Error clearing sales data: {str(e)}'
                )

    def show_context_menu(self, pos):
        """Show context menu for table"""
        menu = QMenu(self)
        
        # Get the row at the click position
        row = self.table.rowAt(pos.y())
        if row >= 0:
            copy_action = menu.addAction("Copy Row Data")
            copy_action.triggered.connect(lambda: self.copy_row_data(row))
        
        menu.exec_(self.table.viewport().mapToGlobal(pos))
    
    def copy_row_data(self, row):
        """Copy row data to clipboard in a formatted way"""
        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        row_data = [self.table.item(row, i).text() if self.table.item(row, i) else "" for i in range(self.table.columnCount())]
        
        # Format as key-value pairs
        formatted_data = []
        for header, value in zip(headers, row_data):
            formatted_data.append(f"{header}: {value}")
        
        # Copy to clipboard
        QApplication.clipboard().setText("\n".join(formatted_data))
