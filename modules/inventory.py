import os
import json
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QScrollArea, QFrame,
                             QFileDialog, QMessageBox, QGridLayout, QDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor
import shutil

class InventoryWidget(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.app_icon = QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icon.png'))
        self.theme_manager = parent.theme_manager if hasattr(parent, 'theme_manager') else None
        self.setup_ui()
        self.refresh_inventory()
        
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.update_style)
            
    def update_style(self):
        if not self.theme_manager:
            return
            
        theme = self.theme_manager.get_theme()
        self.setStyleSheet(f"""
            QWidget#inventoryContainer {{
                background-color: {theme['background']};
            }}
            QPushButton {{
                background-color: #0D6EFD;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #0B5ED7;
            }}
        """)
        
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Search and Add Item section
        top_section = QHBoxLayout()
        top_section.setSpacing(10)
        
        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search inventory...")
        self.search_bar.textChanged.connect(self.refresh_inventory)
        top_section.addWidget(self.search_bar)
        
        # Add Item button
        add_button = QPushButton("Add Item")
        add_button.clicked.connect(self.add_item)
        top_section.addWidget(add_button)
        
        main_layout.addLayout(top_section)
        
        # Scroll area for inventory items
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)  # Remove the border
        
        # Container widget for grid
        self.container = QWidget()
        self.container.setObjectName("inventoryContainer")
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(0, 10, 0, 0)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)  # Align to top-left
        
        self.container.setLayout(self.grid_layout)
        self.scroll.setWidget(self.container)
        
        main_layout.addWidget(self.scroll)
        self.setLayout(main_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh_inventory()  # Refresh layout when widget is resized

    def calculate_columns(self):
        # Get the available width (accounting for scroll bar and margins)
        scroll_width = self.scroll.width() - 25  # Subtract scrollbar width
        min_card_width = 250  # Minimum card width
        spacing = self.grid_layout.spacing()
        margins = self.grid_layout.contentsMargins()
        
        # Calculate available width accounting for margins
        available_width = scroll_width - margins.left() - margins.right()
        
        # Calculate how many cards can fit
        columns = max(1, (available_width + spacing) // (min_card_width + spacing))
        
        return int(columns)

    def refresh_inventory(self):
        # Clear existing items
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get filtered items
        search_text = self.search_bar.text().lower()
        items = self.db.get_inventory()
        filtered_items = [
            item for item in items
            if search_text in item['name'].lower() or 
               search_text in item.get('description', '').lower()
        ]
        
        # Calculate number of columns based on available width
        columns = self.calculate_columns()
        
        # Calculate optimal card width based on available space
        available_width = self.scroll.width() - 25  # Subtract scrollbar width
        margins = self.grid_layout.contentsMargins()
        spacing = self.grid_layout.spacing()
        total_spacing = spacing * (columns - 1)
        total_margins = margins.left() + margins.right()
        card_width = (available_width - total_spacing - total_margins) // columns
        
        # Add items to grid
        for i, item in enumerate(filtered_items):
            row = i // columns
            col = i % columns
            card = InventoryCard(item, self.db, self)
            card.setFixedWidth(card_width)
            self.grid_layout.addWidget(card, row, col)

    def add_item(self):
        dialog = AddItemDialog(self.db, self)
        if dialog.exec():
            self.refresh_inventory()
            
class InventoryCard(QFrame):
    def __init__(self, item_data, db, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.db = db
        self.theme_manager = parent.theme_manager if hasattr(parent, 'theme_manager') else None
        self.setup_ui()
        self.update_style()
        
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.update_style)
        
    def update_style(self):
        if not self.theme_manager:
            return
            
        theme = self.theme_manager.get_theme()
        self.setStyleSheet(f"""
            QLabel {{
                color: {theme['text']};
            }}
            QPushButton {{
                background-color: #0D6EFD;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton#countButton {{
                padding: 4px;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
            }}
            QPushButton:hover {{
                background-color: #0B5ED7;
            }}
        """)
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Content section (image, name, description, url)
        content_layout = QVBoxLayout()
        content_layout.setSpacing(8)
        
        # Image
        image_label = QLabel()
        if self.item_data.get('image'):
            pixmap = QPixmap(self.item_data['image'])
            scaled_pixmap = pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, 
                                        Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
        else:
            image_label.setText("No Image")
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(image_label)
        
        # Item Name
        name_label = QLabel(self.item_data['name'])
        name_font = QFont()
        name_font.setPointSize(12)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        content_layout.addWidget(name_label)
        
        # Description (if exists)
        if self.item_data.get('description'):
            desc_label = QLabel(self.item_data['description'])
            desc_label.setWordWrap(True)
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addWidget(desc_label)
        else:
            # Add spacer if no description
            content_layout.addSpacing(20)
            
        # URL (if exists)
        if self.item_data.get('url'):
            url_label = QLabel(f"<a href='{self.item_data['url']}' style='color: #0D6EFD;'>View Item</a>")
            url_label.setOpenExternalLinks(True)
            url_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addWidget(url_label)
        else:
            # Add spacer if no URL
            content_layout.addSpacing(20)
            
        # Add content section to main layout
        layout.addLayout(content_layout)
        
        # Add fixed spacing before controls
        layout.addSpacing(20)
        
        # Controls section (count controls and edit button)
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(10)
        
        # Count controls
        count_layout = QHBoxLayout()
        count_layout.setSpacing(8)
        
        minus_btn = QPushButton("−")  # Using proper minus sign
        minus_btn.setObjectName("countButton")
        minus_btn.clicked.connect(self.decrease_count)
        count_layout.addWidget(minus_btn)
        
        self.count_label = QLabel(str(self.item_data['count']))
        count_font = QFont()
        count_font.setPointSize(14)
        count_font.setBold(True)
        self.count_label.setFont(count_font)
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setMinimumWidth(40)
        count_layout.addWidget(self.count_label)
        
        plus_btn = QPushButton("+")
        plus_btn.setObjectName("countButton")
        plus_btn.clicked.connect(self.increase_count)
        count_layout.addWidget(plus_btn)
        
        controls_layout.addLayout(count_layout)
        
        # Edit button
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.edit_item)
        controls_layout.addWidget(edit_button)
        
        # Add controls section to main layout
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)
        
    def increase_count(self):
        self.item_data['count'] += 1
        self.count_label.setText(str(self.item_data['count']))
        self.db.update_inventory_item(self.item_data)
        
    def decrease_count(self):
        if self.item_data['count'] > 0:
            self.item_data['count'] -= 1
            self.count_label.setText(str(self.item_data['count']))
            self.db.update_inventory_item(self.item_data)
            
    def edit_item(self):
        dialog = AddItemDialog(self.db, self, self.item_data)
        if dialog.exec():
            # Find the InventoryWidget instance
            parent = self.parent()
            while parent and not isinstance(parent, InventoryWidget):
                parent = parent.parent()
            if parent:
                parent.refresh_inventory()

class AddItemDialog(QDialog):
    def __init__(self, db, parent=None, item_data=None):
        super().__init__(parent)
        self.db = db
        self.item_data = item_data
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Add Item" if not self.item_data else "Edit Item")
        layout = QVBoxLayout()
        
        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_input = QLineEdit()
        if self.item_data:
            self.name_input.setText(self.item_data['name'])
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.desc_input = QLineEdit()
        if self.item_data:
            self.desc_input.setText(self.item_data.get('description', ''))
        desc_layout.addWidget(self.desc_input)
        layout.addLayout(desc_layout)
        
        # Count
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Count:"))
        self.count_input = QLineEdit()
        if self.item_data:
            self.count_input.setText(str(self.item_data['count']))
        count_layout.addWidget(self.count_input)
        layout.addLayout(count_layout)
        
        # URL
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL:"))
        self.url_input = QLineEdit()
        if self.item_data:
            self.url_input.setText(self.item_data.get('url', ''))
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)
        
        # Image
        image_layout = QHBoxLayout()
        image_layout.addWidget(QLabel("Image:"))
        self.image_path = self.item_data.get('image', '') if self.item_data else ''
        self.image_label = QLabel(os.path.basename(self.image_path) if self.image_path else "No image selected")
        image_layout.addWidget(self.image_label)
        image_button = QPushButton("Choose Image")
        image_button.clicked.connect(self.choose_image)
        image_layout.addWidget(image_button)
        layout.addLayout(image_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_item)
        button_layout.addWidget(save_button)
        
        if self.item_data:
            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(self.delete_item)
            button_layout.addWidget(delete_button)
            
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def choose_image(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp)")
        if file_name:
            self.image_path = file_name
            self.image_label.setText(os.path.basename(file_name))
            
    def save_item(self):
        name = self.name_input.text().strip()
        description = self.desc_input.text().strip()
        count = self.count_input.text().strip()
        url = self.url_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Error", "Name is required")
            return
            
        try:
            count = int(count)
        except ValueError:
            QMessageBox.warning(self, "Error", "Count must be a number")
            return
            
        item_data = {
            'name': name,
            'description': description,
            'count': count,
            'url': url,
        }
        
        if self.image_path:
            item_data['image'] = self.image_path
            
        if self.item_data:
            # Editing existing item
            item_data['id'] = self.item_data['id']
            self.db.update_inventory_item(item_data)
        else:
            # Adding new item
            self.db.add_inventory_item(item_data)
            
        self.accept()
        
    def delete_item(self):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete {self.item_data['name']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_inventory_item(self.item_data['id'])
            self.accept()
