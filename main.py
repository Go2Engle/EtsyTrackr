import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                           QTabWidget, QFileDialog, QMessageBox, QDialog)
from PySide6.QtCore import QSettings
from PySide6.QtGui import QIcon
from modules.dashboard import DashboardWidget
from modules.expenses import ExpensesWidget
from modules.settings import SettingsWidget
from modules.sales import SalesWidget
from modules.inventory import InventoryWidget
from modules.database import Database
from modules.welcome import WelcomeDialog
from modules.theme import ThemeManager
from modules.sidebar import Sidebar, MainContent

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EtsyTrackr")
        self.setMinimumSize(1200, 800)
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Initialize settings and theme
        self.settings = QSettings('EtsyTracker', 'EtsyTracker')
        self.theme_manager = ThemeManager()
        self.theme_manager.apply_theme()
        
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
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create sidebar
        self.sidebar = Sidebar(self.theme_manager)
        layout.addWidget(self.sidebar)
        
        # Create main content area
        self.main_content = MainContent()
        
        # Create and add dashboard (index 0)
        self.dashboard = DashboardWidget(self.db, self.theme_manager, None)
        self.main_content.add_widget(self.dashboard, "Dashboard")
        
        # Create and add sales (index 1)
        self.sales = SalesWidget(self.db, self.theme_manager)
        self.main_content.add_widget(self.sales, "Sales")
        
        # Create and add expenses (index 2)
        self.expenses = ExpensesWidget(self.db)
        self.main_content.add_widget(self.expenses, "Expenses")
        
        # Create and add inventory (index 3)
        self.inventory = InventoryWidget(self.db)
        self.main_content.add_widget(self.inventory, "Inventory")
        
        # Create and add settings (index 4)
        self.settings_widget = SettingsWidget(self.settings, self.db, self.theme_manager)
        self.main_content.add_widget(self.settings_widget, "Settings")
        
        # Connect sidebar signals
        self.sidebar.page_changed.connect(self.main_content.setCurrentIndex)
        
        # Add main content to layout
        layout.addWidget(self.main_content)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
