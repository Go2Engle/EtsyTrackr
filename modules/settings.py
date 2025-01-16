from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFileDialog, QMessageBox, QFrame)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
import os
import shutil

class SettingsWidget(QWidget):
    storage_location_changed = Signal(str)
    
    def __init__(self, settings, db, theme_manager=None):
        super().__init__()
        self.theme_manager = theme_manager
        self.app_icon = QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icon.png'))
        self.settings = settings
        self.db = db
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(24)  # Increased spacing between sections
        
        # Theme Section
        if self.theme_manager:
            theme_section = self.create_section("Appearance")
            theme_section_layout = theme_section.layout()
            
            # Theme toggle
            theme_layout = QHBoxLayout()
            theme_label = QLabel("Dark Mode")
            theme_layout.addWidget(theme_label)
            
            theme_toggle = QPushButton("Toggle Theme")
            theme_toggle.setFixedWidth(120)
            theme_toggle.clicked.connect(self.toggle_theme)
            theme_layout.addWidget(theme_toggle)
            theme_layout.addStretch()
            
            theme_section_layout.addLayout(theme_layout)
            layout.addWidget(theme_section)
        
        # Storage Location Section
        storage_section = self.create_section("Data Storage")
        storage_section_layout = storage_section.layout()
        
        # Current location
        current_location = QLabel(f"Current Location: {self.settings.value('storage_location')}")
        storage_section_layout.addWidget(current_location)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Change location button
        change_btn = QPushButton("Change Location")
        change_btn.clicked.connect(self.change_storage_location)
        buttons_layout.addWidget(change_btn)
        
        # Migrate data button
        migrate_btn = QPushButton("Migrate Data")
        migrate_btn.clicked.connect(self.migrate_data)
        buttons_layout.addWidget(migrate_btn)
        buttons_layout.addStretch()
        
        storage_section_layout.addLayout(buttons_layout)
        
        # Add some spacing
        storage_section_layout.addSpacing(20)
        
        layout.addWidget(storage_section)
        
        # Add stretch at the end
        layout.addStretch()
        self.setLayout(layout)
    
    def create_section(self, title):
        """Create a styled section with title"""
        section = QFrame()
        section.setObjectName("settingsSection")
        
        layout = QVBoxLayout()
        layout.setSpacing(16)
        
        # Header
        header = QLabel(title)
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(header)
        
        section.setLayout(layout)
        return section
    
    def toggle_theme(self):
        if self.theme_manager:
            self.theme_manager.toggle_theme()
    
    def change_storage_location(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        if dialog.exec():
            new_path = dialog.selectedFiles()[0]
            
            # Confirm change
            msg = QMessageBox()
            msg.setWindowIcon(self.app_icon)
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setWindowTitle("Storage Location")
            msg.setText("Change Data Directory")
            msg.setInformativeText("This will only change where new files are stored. "
                                "Use the 'Migrate Data' button to move existing files. "
                                "Continue?")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if msg.exec() == QMessageBox.StandardButton.Yes:
                self.settings.setValue('storage_location', new_path)
                self.db.update_storage_location(new_path)
                
                # Update the displayed location
                self.refresh_ui()
                
                QMessageBox.information(self, "Storage Location Changed", 
                    "Storage location updated successfully. New data will be stored here.")
                
                # Emit signal for other components to update
                self.storage_location_changed.emit(new_path)
    
    def migrate_data(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        if dialog.exec():
            new_path = dialog.selectedFiles()[0]
            
            # Don't migrate if source and destination are the same
            if new_path == self.settings.value('storage_location'):
                QMessageBox.warning(self, "Storage Location Error", 
                    "New location is the same as the current location.")
                return
            
            try:
                # Create new directories
                os.makedirs(os.path.join(new_path, 'receipts'), exist_ok=True)
                os.makedirs(os.path.join(new_path, 'statements'), exist_ok=True)
                
                # Copy expenses file
                if os.path.exists(self.db.expenses_file):
                    shutil.copy2(
                        self.db.expenses_file,
                        os.path.join(new_path, 'expenses.json')
                    )
                
                # Copy all receipts
                for item in os.listdir(self.db.receipts_dir):
                    src = os.path.join(self.db.receipts_dir, item)
                    if os.path.isfile(src):
                        shutil.copy2(src, os.path.join(new_path, 'receipts', item))
                
                # Copy all statements
                for item in os.listdir(self.db.statements_dir):
                    src = os.path.join(self.db.statements_dir, item)
                    if os.path.isfile(src):
                        shutil.copy2(src, os.path.join(new_path, 'statements', item))
                
                # Update settings and database
                self.settings.setValue('storage_location', new_path)
                self.db.update_storage_location(new_path)
                
                # Update the displayed location
                self.refresh_ui()
                
                QMessageBox.information(self, "Storage Location Changed", 
                    "All data has been migrated to the new location successfully.")
                
            except Exception as e:
                QMessageBox.critical(self, "Storage Location Error", 
                    f"Failed to migrate data: {str(e)}")
    
    def refresh_ui(self):
        # Recreate the UI to show updated values
        # First, remove the old layout
        if self.layout():
            QWidget().setLayout(self.layout())
        self.setup_ui()
