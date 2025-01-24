from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFileDialog, QMessageBox, QFrame,
                           QComboBox, QTextEdit, QLineEdit, QSizePolicy, QGridLayout,
                           QScrollArea)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
import os
import shutil
import webbrowser
import urllib.parse
from .version import VersionChecker

class SettingsWidget(QWidget):
    storage_location_changed = Signal(str)
    
    def __init__(self, settings, db, theme_manager=None):
        super().__init__()
        self.theme_manager = theme_manager
        self.app_icon = QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icon.png'))
        self.settings = settings
        self.db = db
        
        # Create main scroll area that wraps everything
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Style for scroll area
        scroll_style = """
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: palette(base);
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: palette(mid);
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """
        scroll_area.setStyleSheet(scroll_style)
        
        # Create container widget for all content
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(24)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Add all sections to the container layout
        self.setup_ui(layout)
        
        # Set the container as the scroll area widget
        scroll_area.setWidget(container)
        
        # Add scroll area to the main widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
    
    def setup_ui(self, layout):
        """Setup all UI sections"""
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
        
        # Support Section
        support_section = self.create_section("Support Development")
        support_section_layout = support_section.layout()
        
        donate_layout = QHBoxLayout()
        donate_label = QLabel("If you find EtsyTrackr helpful, consider supporting its development:")
        donate_layout.addWidget(donate_label)
        
        donate_button = QPushButton("Donate")
        donate_button.setFixedWidth(120)
        donate_button.clicked.connect(lambda: webbrowser.open('https://donate.stripe.com/dR614U9az5Wig9O7ss'))
        donate_layout.addWidget(donate_button)
        donate_layout.addStretch()
        
        support_section_layout.addLayout(donate_layout)
        layout.addWidget(support_section)

        # Feature/Bug Request Section
        request_section = self.create_section("Submit Feature/Bug Request")
        request_section_layout = request_section.layout()
        request_section_layout.setSpacing(16)  # Increase spacing between elements

        # Add informative note about submission process
        note_label = QLabel("Note: When you click submit, you'll be taken to GitHub to finalize your submission. "
                          "You can add any screenshots or additional details on the GitHub page.")
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: palette(text); font-style: italic; margin-bottom: 12px;")
        request_section_layout.addWidget(note_label)

        # Modern styling for input fields
        input_style = """
            QLineEdit, QTextEdit {
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 8px;
                background-color: palette(base);
                color: palette(text);
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #0078d4;
                outline: none;
            }
            QComboBox {
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 4px 8px;
                background-color: palette(base);
                color: palette(text);
                min-width: 150px;
            }
            QComboBox:focus {
                border: 2px solid #0078d4;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QLabel {
                margin-bottom: 4px;
                color: palette(text);
            }
        """
        request_section.setStyleSheet(input_style)

        # Request type dropdown with label in form layout
        grid_layout = QGridLayout()
        grid_layout.setSpacing(16)  # Space between elements
        grid_layout.setContentsMargins(0, 0, 0, 16)  # Bottom margin
        
        # Request Type row
        type_label = QLabel("Request Type:")
        type_label.setFixedWidth(150)  # Fixed width for all labels
        self.request_type = QComboBox()
        self.request_type.addItems(["Feature Request", "Bug Report"])
        self.request_type.currentTextChanged.connect(self.update_request_fields)
        self.request_type.setFixedWidth(200)
        grid_layout.addWidget(type_label, 0, 0)
        grid_layout.addWidget(self.request_type, 0, 1)
        
        # Title row
        title_label = QLabel("Title:")
        title_label.setFixedWidth(150)  # Fixed width for all labels
        self.request_title = QLineEdit()
        self.request_title.setPlaceholderText("Brief description of your request")
        grid_layout.addWidget(title_label, 1, 0)
        grid_layout.addWidget(self.request_title, 1, 1)
        
        request_section_layout.addLayout(grid_layout)

        # Feature request fields
        self.feature_widget = QWidget()
        feature_layout = QGridLayout(self.feature_widget)
        feature_layout.setSpacing(16)
        feature_layout.setContentsMargins(0, 0, 0, 0)
        
        # Description field
        desc_label = QLabel("Feature Description:")
        desc_label.setFixedWidth(150)  # Fixed width for all labels
        self.feature_description = QTextEdit()
        self.feature_description.setPlaceholderText("Describe the feature you'd like to see")
        self.feature_description.setMinimumHeight(100)
        feature_layout.addWidget(desc_label, 0, 0, Qt.AlignTop)
        feature_layout.addWidget(self.feature_description, 0, 1)
        
        # Use case field
        use_case_label = QLabel("Use Case:")
        use_case_label.setFixedWidth(150)  # Fixed width for all labels
        self.use_case = QTextEdit()
        self.use_case.setPlaceholderText("How would this feature help you use EtsyTrackr better?")
        self.use_case.setMinimumHeight(80)
        feature_layout.addWidget(use_case_label, 1, 0, Qt.AlignTop)
        feature_layout.addWidget(self.use_case, 1, 1)
        
        # Alternatives field
        alt_label = QLabel("Alternatives Considered:")
        alt_label.setFixedWidth(150)  # Fixed width for all labels
        self.alternatives = QTextEdit()
        self.alternatives.setPlaceholderText("Are there any workarounds or alternatives you're currently using?")
        self.alternatives.setMinimumHeight(80)
        feature_layout.addWidget(alt_label, 2, 0, Qt.AlignTop)
        feature_layout.addWidget(self.alternatives, 2, 1)
        
        # Set column stretch to make text boxes expand
        feature_layout.setColumnStretch(1, 1)
        
        # Bug report fields
        self.bug_widget = QWidget()
        bug_layout = QGridLayout(self.bug_widget)
        bug_layout.setSpacing(16)
        bug_layout.setContentsMargins(0, 0, 0, 0)
        
        # Description field
        bug_desc_label = QLabel("Bug Description:")
        bug_desc_label.setFixedWidth(150)  # Fixed width for all labels
        self.bug_description = QTextEdit()
        self.bug_description.setPlaceholderText("Describe what happened")
        self.bug_description.setMinimumHeight(100)
        bug_layout.addWidget(bug_desc_label, 0, 0, Qt.AlignTop)
        bug_layout.addWidget(self.bug_description, 0, 1)
        
        # Steps field
        steps_label = QLabel("Steps to Reproduce:")
        steps_label.setFixedWidth(150)  # Fixed width for all labels
        self.steps = QTextEdit()
        self.steps.setPlaceholderText("1. Go to '...'\n2. Click on '...'\n3. See error")
        self.steps.setMinimumHeight(80)
        bug_layout.addWidget(steps_label, 1, 0, Qt.AlignTop)
        bug_layout.addWidget(self.steps, 1, 1)
        
        # Expected behavior field
        expected_label = QLabel("Expected Behavior:")
        expected_label.setFixedWidth(150)  # Fixed width for all labels
        self.expected = QTextEdit()
        self.expected.setPlaceholderText("What did you expect to happen?")
        self.expected.setMinimumHeight(80)
        bug_layout.addWidget(expected_label, 2, 0, Qt.AlignTop)
        bug_layout.addWidget(self.expected, 2, 1)
        
        # Set column stretch to make text boxes expand
        bug_layout.setColumnStretch(1, 1)
        
        # Add both widgets to layout
        request_section_layout.addWidget(self.feature_widget)
        request_section_layout.addWidget(self.bug_widget)
        
        # Initially show feature request fields
        self.update_request_fields("Feature Request")

        # Submit button
        submit_layout = QHBoxLayout()
        submit_layout.addStretch()
        submit_button = QPushButton("Submit on GitHub")
        submit_button.clicked.connect(self.submit_request)
        submit_layout.addWidget(submit_button)
        request_section_layout.addLayout(submit_layout)

        layout.addWidget(request_section)
        
        # Add a subtle version number at the bottom right
        version_label = QLabel(f"v{VersionChecker.CURRENT_VERSION.lstrip('v')}")
        version_label.setStyleSheet("color: gray;")
        version_label.setAlignment(Qt.AlignRight)
        layout.addStretch()  # This pushes the version to the bottom
        layout.addWidget(version_label)
    
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
        self.setup_ui(self.layout())
    
    def update_request_fields(self, request_type):
        """Update visible fields based on request type"""
        is_feature = request_type == "Feature Request"
        self.feature_widget.setVisible(is_feature)
        self.bug_widget.setVisible(not is_feature)

    def submit_request(self):
        """Submit a feature request or bug report to GitHub"""
        if not self.request_title.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please provide a title for your request.")
            return

        # Determine the issue type and template
        is_feature = self.request_type.currentText() == "Feature Request"
        template = "feature_request" if is_feature else "bug_report"
        
        # Build the issue URL with pre-filled template
        base_url = "https://github.com/Go2Engle/EtsyTrackr/issues/new"
        
        # Common parameters
        params = {
            'template': f'{template}.yml',
            'title': self.request_title.text()  # GitHub will prepend [Feature]: or [Bug]: from the template
        }
        
        # Add template-specific fields
        if is_feature:
            if not self.feature_description.toPlainText().strip():
                QMessageBox.warning(self, "Validation Error", "Please provide a feature description.")
                return
                
            params.update({
                'description': self.feature_description.toPlainText(),
                'usecase': self.use_case.toPlainText(),
                'alternatives': self.alternatives.toPlainText()
            })
        else:
            if not self.bug_description.toPlainText().strip():
                QMessageBox.warning(self, "Validation Error", "Please provide a bug description.")
                return
            if not self.steps.toPlainText().strip():
                QMessageBox.warning(self, "Validation Error", "Please provide steps to reproduce.")
                return
                
            params.update({
                'description': self.bug_description.toPlainText(),
                'steps': self.steps.toPlainText(),
                'version': VersionChecker.CURRENT_VERSION,
                'expected': self.expected.toPlainText() or 'N/A'
            })
        
        # Build the URL with parameters
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        # Open the GitHub issue page in the default browser
        webbrowser.open(url)
        
        # Clear the form
        self.request_title.clear()
        self.feature_description.clear()
        self.use_case.clear()
        self.alternatives.clear()
        self.bug_description.clear()
        self.steps.clear()
        self.expected.clear()
