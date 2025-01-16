from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt, QSettings, QObject, Signal
from PySide6.QtWidgets import QApplication

class ThemeManager(QObject):
    theme_changed = Signal(bool)  # Signal to notify when theme changes, bool indicates dark mode
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings('EtsyTracker', 'EtsyTracker')
        self._dark_mode = self.settings.value('dark_mode', True, type=bool)
        self.light_theme = {
            'primary': '#1a73e8',  # Google Blue
            'secondary': '#8ab4f8',
            'background': '#ffffff',
            'surface': '#f8f9fa',
            'border': '#dadce0',
            'text': '#202124',
            'text_secondary': '#5f6368',
            'success': '#34a853',  # Google Green
            'warning': '#fbbc04',  # Google Yellow
            'error': '#ea4335',    # Google Red
            'card_shadow': '0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15)',
        }
        self.dark_theme = {
            'primary': '#8ab4f8',  # Light Blue
            'secondary': '#1a73e8',
            'background': '#202124',
            'surface': '#292a2d',
            'border': '#5f6368',
            'text': '#e8eaed',
            'text_secondary': '#9aa0a6',
            'success': '#81c995',  # Light Green
            'warning': '#fdd663',  # Light Yellow
            'error': '#f28b82',    # Light Red
            'card_shadow': '0 1px 2px 0 rgba(0,0,0,0.3), 0 1px 3px 1px rgba(0,0,0,0.15)',
        }
        
    def get_light_theme(self):
        return self.light_theme
    
    def get_dark_theme(self):
        return self.dark_theme
    
    def get_theme(self):
        return self.get_dark_theme() if self._dark_mode else self.get_light_theme()
    
    def is_dark_mode(self):
        return self._dark_mode
    
    def toggle_theme(self):
        self._dark_mode = not self._dark_mode
        self.settings.setValue('dark_mode', self._dark_mode)
        self.apply_theme()
        self.theme_changed.emit(self._dark_mode)
    
    def apply_theme(self):
        self.settings.setValue('dark_mode', self._dark_mode)
        theme = self.get_theme()
        
        # Create the base palette
        palette = QPalette()
        
        # Set window/widget colors
        palette.setColor(QPalette.Window, QColor(theme['background']))
        palette.setColor(QPalette.WindowText, QColor(theme['text']))
        palette.setColor(QPalette.Base, QColor(theme['surface']))
        palette.setColor(QPalette.AlternateBase, QColor(theme['surface']))
        palette.setColor(QPalette.Text, QColor(theme['text']))
        palette.setColor(QPalette.Button, QColor(theme['surface']))
        palette.setColor(QPalette.ButtonText, QColor(theme['text']))
        palette.setColor(QPalette.Link, QColor(theme['primary']))
        palette.setColor(QPalette.LinkVisited, QColor(theme['secondary']))
        
        # Set disabled colors
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(theme['text_secondary']))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(theme['text_secondary']))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(theme['text_secondary']))
        
        # Set highlight colors
        palette.setColor(QPalette.Highlight, QColor(theme['primary']))
        palette.setColor(QPalette.HighlightedText, QColor(theme['background']))
        
        # Apply the palette
        app = QApplication.instance()
        app.setPalette(palette)
        
        # Apply stylesheet
        style = f"""
            QWidget {{
                color: {theme['text']};
                background-color: {theme['background']};
            }}
            
            QMessageBox {{
                background-color: {theme['surface']};
                color: {theme['text']};
            }}
            
            QMessageBox QLabel {{
                color: {theme['text']};
                background-color: transparent;
            }}
            
            QMessageBox QPushButton {{
                background-color: {theme['primary']};
                color: {theme['background']};
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
                min-width: 80px;
            }}
            
            QMessageBox QPushButton:hover {{
                background-color: {theme['secondary']};
            }}
            
            QMainWindow {{
                background-color: {theme['background']};
            }}
            
            QWidget {{
                color: {theme['text']};
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell, "Helvetica Neue", sans-serif;
            }}
            
            #sidebar {{
                background-color: {theme['surface']};
            }}
            
            #sidebarTitle {{
                color: {theme['primary']};
                font-size: 20px;
                font-weight: bold;
                padding: 16px;
            }}
            
            #sidebarButton {{
                background-color: transparent;
                border: none;
                border-radius: 8px;
                color: {theme['text_secondary']};
                text-align: left;
                padding: 8px 16px;
            }}
            
            #sidebarButton:hover {{
                background-color: {'rgba(255, 255, 255, 0.12)' if self._dark_mode else 'rgba(0, 0, 0, 0.04)'};
                color: {'#ffffff' if self._dark_mode else theme['text']};
            }}
            
            #sidebarButton:checked {{
                background-color: {theme['primary']};
                color: #ffffff;
            }}
            
            #appLogo {{
                width: 24px;
                height: 24px;
                margin-right: 8px;
            }}
            
            #mainContent {{
                background-color: {theme['background']};
            }}
            
            QTabWidget::pane {{
                border: 1px solid {theme['border']};
                border-radius: 8px;
                background-color: {theme['surface']};
                margin-top: -1px;
            }}
            
            QTabBar::tab {{
                background-color: transparent;
                color: {theme['text_secondary']};
                padding: 8px 16px;
                margin: 0 4px;
                border: none;
                border-radius: 8px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {theme['primary']};
                color: {'#ffffff' if self._dark_mode else theme['background']};
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {theme['surface']};
                color: {theme['text']};
            }}
            
            QPushButton {{
                background-color: {theme['primary']};
                color: {'#ffffff' if self._dark_mode else theme['background']};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            
            QPushButton:hover {{
                background-color: {theme['secondary']};
            }}
            
            QPushButton:pressed {{
                background-color: {theme['primary']};
            }}
            
            QPushButton:disabled {{
                background-color: {theme['surface']};
                color: {theme['text_secondary']};
            }}
            
            QLineEdit, QComboBox, QSpinBox {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                border-radius: 4px;
                padding: 8px;
            }}
            
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
                border: 2px solid {theme['primary']};
                padding: 7px;
            }}
            
            QComboBox::drop-down {{
                border: none;
                padding-right: 8px;
            }}
            
            QTableView {{
                background-color: {theme['background']};
                border: 1px solid {theme['border']};
                border-radius: 8px;
                gridline-color: {theme['border']};
                alternate-background-color: {theme['surface']};
                selection-background-color: {theme['primary']};
                selection-color: #ffffff;
            }}
            
            QTableView::item {{
                padding: 2px;
                min-height: 24px;
            }}
            
            QTableView::item:selected {{
                background-color: {theme['primary']};
                color: {'#ffffff' if self._dark_mode else theme['background']};
            }}
            
            QHeaderView::section {{
                padding: 4px;
                min-height: 24px;
                background-color: {theme['surface']};
                border: none;
                border-bottom: 1px solid {theme['border']};
            }}
            
            QScrollBar:vertical {{
                background-color: {theme['surface']};
                width: 12px;
                margin: 0;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {theme['border']};
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            
            QScrollBar:horizontal {{
                background-color: {theme['surface']};
                height: 12px;
                margin: 0;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {theme['border']};
                border-radius: 6px;
                min-width: 20px;
                margin: 2px;
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
            
            QDateEdit {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 24px;
            }}
            
            QDateEdit::drop-down {{
                border: none;
                width: 20px;
            }}
            
            QDateEdit::down-arrow {{
                image: none;
                width: 12px;
                height: 12px;
            }}
            
            QCalendarWidget {{
                background-color: {theme['background']};
                color: {theme['text']};
            }}
            
            QCalendarWidget QWidget {{
                background-color: {theme['background']};
                color: {theme['text']};
            }}
            
            QCalendarWidget QToolButton {{
                color: {theme['text']};
                background-color: transparent;
                padding: 4px;
                border-radius: 4px;
            }}
            
            QCalendarWidget QMenu {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
            }}
            
            QCalendarWidget QSpinBox {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
            }}
            
            QCalendarWidget QAbstractItemView:enabled {{
                background-color: {theme['surface']};
                color: {theme['text']};
                selection-background-color: {theme['primary']};
                selection-color: #ffffff;
            }}
            
            QTableView QPushButton {{
                background-color: {theme['primary']};
                color: {'#ffffff' if self._dark_mode else theme['background']};
                border: none;
                border-radius: 3px;
                padding: 2px;
                min-width: 45px;
                max-width: 45px;
                min-height: 20px;
                max-height: 20px;
                font-size: 11px;
            }}
            
            QTableView QPushButton:hover {{
                background-color: {theme['secondary']};
            }}
            
            /* Context Menu Styling */
            QMenu {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                border-radius: 4px;
                padding: 4px;
            }}
            
            QMenu::item {{
                padding: 6px 24px;
                border-radius: 2px;
            }}
            
            QMenu::item:selected {{
                background-color: {theme['primary']};
                color: #ffffff;
            }}
            
            QMenu::separator {{
                height: 1px;
                background-color: {theme['border']};
                margin: 4px 0px;
            }}
        """
        app.setStyleSheet(style)
