from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, 
                              QFileDialog, QWidget, QRadioButton, QButtonGroup,
                              QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import os
from .theme import ThemeManager

class WelcomeDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.storage_path = None
        self.setWindowTitle("EtsyTrackr")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.theme_manager = ThemeManager()
        self.theme_manager.theme_changed.connect(self.apply_theme)
        self.setup_ui()
        self.apply_theme()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)  
        layout.setContentsMargins(30, 30, 30, 30)  
        
        # Welcome message
        welcome_label = QLabel("Welcome to EtsyTrackr")
        welcome_label.setObjectName("welcomeLabel")
        welcome_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome_label)
        
        # Description
        desc_label = QLabel(
            "Please choose how you would like to set up your data storage:"
        )
        desc_label.setWordWrap(True)
        desc_label.setObjectName("descriptionLabel")
        layout.addWidget(desc_label)
        
        # Radio buttons for options
        self.new_dir_radio = QRadioButton(
            "Create New Data Directory\n"
            "Choose a location for your new Etsy Tracker data. This will create a new directory\n"
            "to store your statements, receipts, and other data."
        )
        self.new_dir_radio.setObjectName("optionRadio")
        
        self.existing_dir_radio = QRadioButton(
            "Use Existing Data Directory\n"
            "Select an existing Etsy Tracker data directory that contains your previous data."
        )
        self.existing_dir_radio.setObjectName("optionRadio")
        
        # Button group
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.new_dir_radio)
        self.button_group.addButton(self.existing_dir_radio)
        self.new_dir_radio.setChecked(True)
        
        layout.addWidget(self.new_dir_radio)
        layout.addWidget(self.existing_dir_radio)
        
        # Add spacer before button
        layout.addStretch()
        
        # Choose directory button
        self.choose_btn = QPushButton("Choose Directory")
        self.choose_btn.setObjectName("primaryButton")
        self.choose_btn.clicked.connect(self.choose_directory)
        layout.addWidget(self.choose_btn, 0, Qt.AlignCenter)  
        
        self.setLayout(layout)
    
    def apply_theme(self):
        theme = self.theme_manager.dark_theme if self.theme_manager.is_dark_mode() else self.theme_manager.light_theme
        
        # Set dialog background
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme['background']};
                color: {theme['text']};
            }}
            #welcomeLabel {{
                font-size: 24px;
                font-weight: bold;
                color: {theme['text']};
            }}
            #descriptionLabel {{
                font-size: 14px;
                color: {theme['text']};
            }}
            #optionRadio {{
                font-size: 13px;
                padding: 10px;
                background-color: {theme['surface']};
                color: {theme['text']};
                border-radius: 5px;
            }}
            #primaryButton {{
                font-size: 14px;
                padding: 12px 24px;
                background-color: {theme['primary']};
                color: {theme['background']};
                border: none;
                border-radius: 5px;
            }}
            #primaryButton:hover {{
                background-color: {theme['secondary']};
            }}
        """)
    
    def verify_existing_directory(self, path):
        """Check if the selected directory is a valid Etsy Tracker data directory"""
        required_dirs = ['receipts', 'statements']
        for dir_name in required_dirs:
            if not os.path.isdir(os.path.join(path, dir_name)):
                return False
        return True
    
    def choose_directory(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        if dialog.exec():
            selected_path = dialog.selectedFiles()[0]
            
            if self.existing_dir_radio.isChecked():
                # Verify it's a valid Etsy Tracker directory
                if not self.verify_existing_directory(selected_path):
                    QMessageBox.warning(
                        self,
                        "Invalid Directory",
                        "The selected directory does not appear to be a valid Etsy Tracker data directory.\n\n"
                        "Please select a directory that contains 'receipts' and 'statements' folders."
                    )
                    return
                    
            self.storage_path = selected_path
            self.accept()
