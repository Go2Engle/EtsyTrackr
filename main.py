import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QTabWidget, QFileDialog, QMessageBox, QDialog)
from PySide6.QtCore import QSettings
from modules.dashboard import DashboardWidget
from modules.expenses import ExpensesWidget
from modules.settings import SettingsWidget
from modules.sales import SalesWidget
from modules.database import Database
from modules.welcome import WelcomeDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Etsy Sales Tracker")
        self.setMinimumSize(1200, 800)
        
        # Initialize settings
        self.settings = QSettings('EtsyTracker', 'EtsyTracker')
        self.init_storage_location()
        
        # Initialize database
        storage_path = self.settings.value('storage_location')
        self.db = Database(storage_path)
        
        # Setup UI
        self.setup_ui()
    
    def init_storage_location(self):
        if not self.settings.value('storage_location'):
            welcome = WelcomeDialog()
            if welcome.exec() == QDialog.Accepted and welcome.storage_path:
                storage_path = welcome.storage_path
                self.settings.setValue('storage_location', storage_path)
                
                # Only create directories if this is a new data directory
                if not os.path.exists(os.path.join(storage_path, 'receipts')):
                    os.makedirs(os.path.join(storage_path, 'receipts'), exist_ok=True)
                    os.makedirs(os.path.join(storage_path, 'statements'), exist_ok=True)
            else:
                # If user cancels, we can't continue
                sys.exit()
    
    def prompt_storage_location(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        if dialog.exec():
            storage_path = dialog.selectedFiles()[0]
            self.settings.setValue('storage_location', storage_path)
            
            # Create necessary subdirectories
            os.makedirs(os.path.join(storage_path, 'receipts'), exist_ok=True)
            os.makedirs(os.path.join(storage_path, 'statements'), exist_ok=True)
    
    def setup_ui(self):
        """Set up the main window UI"""
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Create and add dashboard tab first
        self.dashboard = DashboardWidget(self.db, None)  
        tabs.addTab(self.dashboard, "Dashboard")
        
        # Create and add sales tab
        self.sales = SalesWidget(self.db)
        tabs.addTab(self.sales, "Sales")
        
        # Create and add expenses tab
        self.expenses = ExpensesWidget(self.db)
        tabs.addTab(self.expenses, "Expenses")
        
        # Create and add settings tab
        self.settings_widget = SettingsWidget(self.settings, self.db)
        tabs.addTab(self.settings_widget, "Settings")
        
        # Add tabs to layout
        layout.addWidget(tabs)
        
        # Initial refresh of dashboard
        self.dashboard.refresh_dashboard()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
