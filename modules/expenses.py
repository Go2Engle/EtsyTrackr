from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QFileDialog, QDateEdit,
                           QTableWidget, QTableWidgetItem, QHeaderView,
                           QMessageBox, QMenu, QComboBox)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QCursor
from qtawesome import icon
import os
import json
import shutil
from datetime import datetime
import calendar
import re

class ExpensesWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Filters section
        filter_layout = QHBoxLayout()
        
        # Year filter
        year_label = QLabel("Year:")
        self.year_filter = QComboBox()
        current_year = datetime.now().year
        self.year_filter.addItems(['All Years'] + [str(year) for year in range(current_year, current_year-5, -1)])
        self.year_filter.currentTextChanged.connect(self.refresh_table)
        filter_layout.addWidget(year_label)
        filter_layout.addWidget(self.year_filter)
        
        # Month filter
        month_label = QLabel("Month:")
        self.month_filter = QComboBox()
        self.month_filter.addItems(['All Months'] + list(calendar.month_name)[1:])
        self.month_filter.currentTextChanged.connect(self.refresh_table)
        filter_layout.addWidget(month_label)
        filter_layout.addWidget(self.month_filter)
        
        # Search filter
        search_label = QLabel("Search:")
        self.search_filter = QLineEdit()
        self.search_filter.setPlaceholderText("Filter by description...")
        self.search_filter.textChanged.connect(self.refresh_table)
        filter_layout.addWidget(search_label)
        filter_layout.addWidget(self.search_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Input form
        form_layout = QHBoxLayout()
        
        # Date input
        date_label = QLabel("Date:")
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        
        # Description input
        desc_label = QLabel("Description:")
        self.desc_edit = QLineEdit()
        
        # Amount input
        amount_label = QLabel("Amount:")
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("0.00")
        
        # Category input
        category_label = QLabel("Category:")
        self.category_edit = QLineEdit()
        
        # Receipt upload
        self.upload_btn = QPushButton("Upload Receipt")
        self.upload_btn.clicked.connect(self.upload_receipt)
        
        # Add expense button
        add_btn = QPushButton("Add Expense")
        add_btn.clicked.connect(self.add_expense)
        
        form_layout.addWidget(date_label)
        form_layout.addWidget(self.date_edit)
        form_layout.addWidget(desc_label)
        form_layout.addWidget(self.desc_edit)
        form_layout.addWidget(amount_label)
        form_layout.addWidget(self.amount_edit)
        form_layout.addWidget(category_label)
        form_layout.addWidget(self.category_edit)
        form_layout.addWidget(self.upload_btn)
        form_layout.addWidget(add_btn)
        
        layout.addLayout(form_layout)
        
        # Expenses table
        self.table = QTableWidget()
        self.setup_table()
        
        layout.addWidget(self.table)
        
        # Stats bar
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        # Total expenses
        self.total_expenses_label = QLabel()
        self.total_expenses_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(self.total_expenses_label)
        
        # Number of expenses
        self.num_expenses_label = QLabel()
        self.num_expenses_label.setStyleSheet("font-size: 14px;")
        stats_layout.addWidget(self.num_expenses_label)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        self.setLayout(layout)
        self.refresh_table()
        
        # Store the path of the last selected receipt
        self.current_receipt_path = None
    
    def setup_table(self):
        # Set up the table
        self.table.setColumnCount(4)
        headers = ["Date", "Description", "Amount", "Receipt"]
        self.table.setHorizontalHeaderLabels(headers)
        
        # Enable context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Set column widths
        self.table.setColumnWidth(0, 100)  # Date
        self.table.setColumnWidth(1, 200)  # Description
        self.table.setColumnWidth(2, 80)   # Amount
        self.table.setColumnWidth(3, 50)   # Receipt - Smaller width for compact buttons
        
        # Set table properties
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        
        # Set resize modes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Description column stretches
        for col in [0, 2, 3]:  # Fixed width for other columns
            header.setSectionResizeMode(col, QHeaderView.Fixed)
    
    def upload_receipt(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Select Receipt",
            "",
            "Image Files (*.png *.jpg *.jpeg *.pdf);;All Files (*.*)"
        )
        
        if file_path:
            self.current_receipt_path = file_path
            self.upload_btn.setText("Receipt Selected")
    
    def add_expense(self):
        try:
            # Get form data
            date = self.date_edit.date().toPython()
            description = self.desc_edit.text().strip()
            amount_text = self.amount_edit.text().strip().replace('$', '').replace(',', '')
            category = self.category_edit.text().strip()
            
            # Validate inputs
            if not description:
                QMessageBox.warning(self, "Error", "Please enter a description")
                return
                
            try:
                amount = float(amount_text)
            except ValueError:
                QMessageBox.warning(self, "Error", "Please enter a valid amount")
                return
            
            # Add expense to database
            expense_data = {
                'date': date.strftime('%Y-%m-%d'),
                'description': description,
                'amount': amount,
                'category': category
            }
            
            expense_id = self.db.add_expense(expense_data)
            
            # Handle receipt if one was selected
            if self.current_receipt_path:
                try:
                    # Get file extension
                    _, ext = os.path.splitext(self.current_receipt_path)
                    
                    # Create new filename with expense ID
                    new_filename = f"receipt_{expense_id}{ext}"
                    new_path = os.path.join(self.db.receipts_dir, new_filename)
                    
                    # Copy file to receipts directory
                    shutil.copy2(self.current_receipt_path, new_path)
                    
                    # Update expense with receipt file
                    self.db.update_expense(expense_id, {'receipt_file': new_filename})
                    
                except Exception as e:
                    QMessageBox.warning(self, "Warning", f"Failed to save receipt: {str(e)}")
            
            # Clear form
            self.desc_edit.clear()
            self.amount_edit.clear()
            self.category_edit.clear()
            self.upload_btn.setText("Upload Receipt")
            self.current_receipt_path = None
            
            # Refresh table
            self.refresh_table()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add expense: {str(e)}")
    
    def show_context_menu(self, position):
        menu = QMenu(self)
        delete_action = menu.addAction(icon("fa5s.trash-alt"), "Delete")
        
        # Get the row under the cursor
        row = self.table.rowAt(position.y())
        if row >= 0:  # Only show menu if clicked on a valid row
            action = menu.exec(self.table.viewport().mapToGlobal(position))
            if action == delete_action:
                # Get expense ID from the hidden data in the date column
                date_item = self.table.item(row, 0)
                if date_item:
                    expense_id = date_item.data(Qt.ItemDataRole.UserRole)
                    self.delete_expense(expense_id)
    
    def delete_expense(self, expense_id):
        reply = QMessageBox.question(
            self,
            'Delete Expense',
            'Are you sure you want to delete this expense?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_expense(expense_id)
            self.refresh_table()
    
    def add_expense_to_table(self, row, date, description, amount, category, receipt_filename):
        self.table.setItem(row, 0, QTableWidgetItem(date))
        self.table.setItem(row, 1, QTableWidgetItem(description))
        self.table.setItem(row, 2, QTableWidgetItem(f"${amount:,.2f}"))
        self.table.setItem(row, 3, QTableWidgetItem(category))
        
        # Create view button
        if receipt_filename:
            view_btn = QPushButton("View")
            view_btn.clicked.connect(lambda: self.view_receipt(receipt_filename))
            self.table.setCellWidget(row, 3, view_btn)
        else:
            upload_btn = QPushButton("Upload")
            upload_btn.clicked.connect(lambda: self.upload_receipt_for_expense(row))
            self.table.setCellWidget(row, 3, upload_btn)
        
    def upload_receipt_for_expense(self, expense_id):
        try:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(
                self,
                "Select Receipt",
                "",
                "Image Files (*.png *.jpg *.jpeg *.pdf);;All Files (*.*)"
            )
            
            if file_path:
                # Get file extension
                _, ext = os.path.splitext(file_path)
                
                # Get expense details for filename
                expenses = self.db.get_expenses()
                expense = next((e for e in expenses if e['id'] == expense_id), None)
                
                if expense:
                    # Create descriptive filename:
                    # Format: YYYY-MM-DD_description_expenseID.ext
                    # Replace spaces and special characters in description with underscores
                    safe_description = re.sub(r'[^\w\s-]', '', expense['description'])  # Remove special chars
                    safe_description = re.sub(r'\s+', '_', safe_description.strip())    # Replace spaces with _
                    safe_description = safe_description[:50]  # Limit length
                    
                    new_filename = f"{expense['date']}_{safe_description}_id{expense_id}{ext}"
                    new_path = os.path.join(self.db.receipts_dir, new_filename)
                    
                    # Copy file to receipts directory
                    shutil.copy2(file_path, new_path)
                    
                    # Update expense with receipt file
                    self.db.update_expense(expense_id, new_filename)
                    
                    # Refresh table
                    self.refresh_table()
                else:
                    raise Exception("Expense not found")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to upload receipt: {str(e)}")
    
    def refresh_table(self):
        # Clear table
        self.table.setRowCount(0)
        
        # Load expenses
        expenses = self.db.get_expenses()
        
        # Apply filters
        filtered_expenses = []
        selected_year = self.year_filter.currentText()
        selected_month = self.month_filter.currentText()
        search_text = self.search_filter.text().lower()
        
        for expense in expenses:
            date = datetime.strptime(expense['date'], '%Y-%m-%d')
            
            # Year filter
            if selected_year != 'All Years' and str(date.year) != selected_year:
                continue
                
            # Month filter
            if selected_month != 'All Months' and calendar.month_name[date.month] != selected_month:
                continue
                
            # Search filter
            if search_text and search_text not in expense['description'].lower() and search_text not in expense.get('category', '').lower():
                continue
                
            filtered_expenses.append(expense)
        
        # Update table
        self.table.setRowCount(len(filtered_expenses))
        for row, expense in enumerate(filtered_expenses):
            self.add_expense_to_table(
                row,
                expense['date'],
                expense['description'],
                expense['amount'],
                expense.get('category', ''),  # Handle missing category
                expense.get('receipt_file')
            )
        
        # Update stats
        total_amount = sum(float(expense['amount']) for expense in filtered_expenses)
        num_expenses = len(filtered_expenses)
        
        self.total_expenses_label.setText(f"Total: ${total_amount:,.2f}")
        self.num_expenses_label.setText(f"Count: {num_expenses:,}")
    
    def view_receipt(self, filename):
        receipt_path = os.path.join(self.db.receipts_dir, filename)
        if os.path.exists(receipt_path):
            os.startfile(receipt_path)
        else:
            QMessageBox.warning(self, "Error", "Receipt file not found")
