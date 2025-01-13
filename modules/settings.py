from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, Signal
import os
import shutil

class SettingsWidget(QWidget):
    storage_location_changed = Signal(str)
    
    def __init__(self, settings, db):
        super().__init__()
        self.settings = settings
        self.db = db
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Storage Location Section
        storage_section = QVBoxLayout()
        
        # Header
        storage_header = QLabel("Data Storage")
        storage_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        storage_section.addWidget(storage_header)
        
        # Current location
        current_location = QLabel(f"Current Location: {self.settings.value('storage_location')}")
        storage_section.addWidget(current_location)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Change location button
        change_btn = QPushButton("Change Location")
        change_btn.clicked.connect(self.change_storage_location)
        buttons_layout.addWidget(change_btn)
        
        # Migrate data button
        migrate_btn = QPushButton("Migrate Data to New Location")
        migrate_btn.clicked.connect(self.migrate_data)
        buttons_layout.addWidget(migrate_btn)
        
        storage_section.addLayout(buttons_layout)
        
        # Add some spacing
        storage_section.addSpacing(20)
        
        layout.addLayout(storage_section)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def change_storage_location(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        if dialog.exec():
            new_path = dialog.selectedFiles()[0]
            
            # Confirm change
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setText("Change Storage Location")
            msg.setInformativeText("This will only change where new files are stored. "
                                "Use the 'Migrate Data' button to move existing files. "
                                "Continue?")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if msg.exec() == QMessageBox.StandardButton.Yes:
                self.settings.setValue('storage_location', new_path)
                self.db.update_storage_location(new_path)
                
                # Update the displayed location
                self.refresh_ui()
                
                QMessageBox.information(self, "Success", 
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
                QMessageBox.warning(self, "Error", 
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
                
                QMessageBox.information(self, "Success", 
                    "All data has been migrated to the new location successfully.")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", 
                    f"Failed to migrate data: {str(e)}")
    
    def refresh_ui(self):
        # Recreate the UI to show updated values
        # First, remove the old layout
        if self.layout():
            QWidget().setLayout(self.layout())
        self.setup_ui()
