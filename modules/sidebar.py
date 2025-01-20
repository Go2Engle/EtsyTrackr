from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                              QStackedWidget, QLabel, QFrame, QHBoxLayout)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QIcon
from qtawesome import icon
import os
from .version import VersionChecker

class SidebarButton(QPushButton):
    def __init__(self, text, icon_name, dark_mode=False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setText(text)
        self._icon_name = icon_name
        self._dark_mode = dark_mode
        self._update_icon()
        self.setIconSize(QSize(24, 24))
        self.setMinimumHeight(48)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("sidebarButton")
    
    def set_dark_mode(self, is_dark):
        self._dark_mode = is_dark
        self._update_icon()
    
    def _update_icon(self):
        if self.isChecked():
            # Always white when selected
            color = 'white'
        else:
            # White in dark mode, black in light mode
            color = 'white' if self._dark_mode else 'black'
        
        self.setIcon(icon(self._icon_name, color=color))
    
    def setChecked(self, checked):
        super().setChecked(checked)
        self._update_icon()

class Sidebar(QFrame):
    page_changed = Signal(int)
    
    def __init__(self, theme_manager=None, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFrameStyle(QFrame.NoFrame)
        self.expanded = False
        self.MINIMIZED_WIDTH = 72
        self.EXPANDED_WIDTH = 260
        self.theme_manager = theme_manager
        self._dark_mode = theme_manager.is_dark_mode() if theme_manager else False
        
        if theme_manager:
            theme_manager.theme_changed.connect(self.on_theme_changed)
        
        self.setup_ui()
        
        # Check for updates periodically (every 4 hours)
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.check_for_updates)
        self.update_timer.start(4 * 60 * 60 * 1000)  # 4 hours in milliseconds
        
        # Initial check
        QTimer.singleShot(1000, self.check_for_updates)  # Check after 1 second
    
    def check_for_updates(self):
        """Check for updates and show/hide upgrade button"""
        update_available, latest_version = VersionChecker.check_for_updates()
        if update_available:
            # Remove any 'v' prefix since we'll add it in the text
            version_number = latest_version.lstrip('v')
            self.upgrade_btn.setText(f"Upgrade to v{version_number}")
            self.upgrade_btn.show()
            self.upgrade_spacer.show()
        else:
            self.upgrade_btn.hide()
            self.upgrade_spacer.hide()
    
    def on_upgrade_clicked(self):
        """Open the GitHub releases page"""
        VersionChecker.open_releases_page()
    
    def on_theme_changed(self, is_dark):
        self._dark_mode = is_dark
        for btn in self.buttons:
            btn.set_dark_mode(is_dark)
        icon_name = "fa5s.chevron-right" if not self.expanded else "fa5s.chevron-left"
        self.collapse_btn.setIcon(icon(icon_name, color='white' if is_dark else 'black'))
        self.upgrade_btn.set_dark_mode(is_dark)
        # Update both theme toggle buttons
        self.theme_toggle.set_dark_mode(is_dark)
        self.theme_toggle_expanded.set_dark_mode(is_dark)
        self.theme_toggle.setIcon(icon("fa5s.sun" if is_dark else "fa5s.moon", 
                                    color='white' if is_dark else 'black'))
        self.theme_toggle_expanded.setIcon(icon("fa5s.sun" if is_dark else "fa5s.moon", 
                                    color='white' if is_dark else 'black'))
    
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        if self.theme_manager:
            self.theme_manager.toggle_theme()
            # Update both theme toggle buttons
            icon_name = "fa5s.sun" if self._dark_mode else "fa5s.moon"
            color = 'white' if self._dark_mode else 'black'
            self.theme_toggle.setIcon(icon(icon_name, color=color))
            self.theme_toggle_expanded.setIcon(icon(icon_name, color=color))
            
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 16, 8, 16)
        self.layout.setSpacing(8)
        
        # App title/logo container
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(12, 0, 0, 0)
        
        # App logo
        self.logo = QLabel()
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icon.png')
        if os.path.exists(icon_path):
            self.logo.setPixmap(QIcon(icon_path).pixmap(QSize(24, 24)))
        self.logo.setObjectName("appLogo")
        self.logo.setAttribute(Qt.WA_TranslucentBackground)
        title_layout.addWidget(self.logo)
        
        # App title
        self.title = QLabel("EtsyTrackr")
        self.title.setObjectName("sidebarTitle")
        self.title.setAttribute(Qt.WA_TranslucentBackground)
        self.title.hide()
        title_layout.addWidget(self.title)
        
        title_layout.addStretch()
        self.layout.addLayout(title_layout)
        
        # Add spacing
        self.layout.addSpacing(24)
        
        # Navigation buttons
        self.buttons = []
        self.button_labels = {
            0: "Dashboard",
            1: "Sales",
            2: "Expenses",
            3: "Inventory",
            4: "Settings"
        }
        self.add_nav_button(self.button_labels[0], "fa5s.chart-line", 0)
        self.add_nav_button(self.button_labels[1], "fa5s.shopping-cart", 1)
        self.add_nav_button(self.button_labels[2], "fa5s.receipt", 2)
        self.add_nav_button(self.button_labels[3], "fa5s.boxes", 3)
        self.add_nav_button(self.button_labels[4], "fa5s.cog", 4)
        
        # Set first button as active
        if self.buttons:
            self.buttons[0].setChecked(True)
        
        # Hide text initially since we start minimized
        for btn in self.buttons:
            btn.setText("")
        
        # Add stretch to push upgrade and collapse buttons to bottom
        self.layout.addStretch()
        
        # Upgrade notification button (hidden by default)
        self.upgrade_btn = SidebarButton("Upgrade Available", "fa5s.arrow-circle-up", self._dark_mode)
        self.upgrade_btn.clicked.connect(self.on_upgrade_clicked)
        self.upgrade_btn.setFlat(True)  # Remove the button border
        self.upgrade_btn.hide()
        self.layout.addWidget(self.upgrade_btn)
        
        # Spacer between upgrade and collapse buttons (hidden by default)
        self.upgrade_spacer = QWidget()
        self.upgrade_spacer.setFixedHeight(8)
        self.upgrade_spacer.setStyleSheet("background: transparent; border: none;")
        self.upgrade_spacer.hide()
        self.layout.addWidget(self.upgrade_spacer)
        
        # Bottom container for collapse and theme buttons
        self.bottom_container = QWidget()
        self.bottom_container.setObjectName("bottom_container")
        self.bottom_container.setStyleSheet("background: transparent;")
        bottom_layout = QVBoxLayout(self.bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)
        
        # Create horizontal container for expanded state
        self.expanded_container = QWidget()
        self.expanded_container.setObjectName("expanded_container")
        self.expanded_container.setStyleSheet("background: transparent;")
        expanded_layout = QHBoxLayout(self.expanded_container)
        expanded_layout.setContentsMargins(0, 0, 0, 0)
        expanded_layout.setSpacing(8)
        
        # Theme toggle button for collapsed state
        self.theme_toggle = SidebarButton("", "fa5s.sun" if self._dark_mode else "fa5s.moon", self._dark_mode)
        self.theme_toggle.setCheckable(False)
        self.theme_toggle.clicked.connect(self.toggle_theme)
        self.theme_toggle.setToolTip("Toggle dark/light theme")
        
        # Theme toggle button for expanded state
        self.theme_toggle_expanded = SidebarButton("", "fa5s.sun" if self._dark_mode else "fa5s.moon", self._dark_mode)
        self.theme_toggle_expanded.setCheckable(False)
        self.theme_toggle_expanded.clicked.connect(self.toggle_theme)
        self.theme_toggle_expanded.setToolTip("Toggle dark/light theme")
        
        # Collapse button
        self.collapse_btn = SidebarButton("", "fa5s.chevron-right", self._dark_mode)
        self.collapse_btn.setCheckable(False)
        self.collapse_btn.clicked.connect(self.toggle_sidebar)
        
        # Collapse button for expanded state
        self.collapse_btn_expanded = SidebarButton("", "fa5s.chevron-right", self._dark_mode)
        self.collapse_btn_expanded.setCheckable(False)
        self.collapse_btn_expanded.clicked.connect(self.toggle_sidebar)
        
        # Add buttons to layouts
        expanded_layout.addWidget(self.collapse_btn_expanded)
        expanded_layout.addStretch()
        expanded_layout.addWidget(self.theme_toggle_expanded)
        
        # Stack the buttons vertically for collapsed state
        bottom_layout.addWidget(self.theme_toggle)
        bottom_layout.addWidget(self.collapse_btn)
        
        # Add both containers to the main layout
        self.layout.addWidget(self.expanded_container)
        self.layout.addWidget(self.bottom_container)
        
        # Initially show collapsed layout
        self.expanded_container.hide()
        self.bottom_container.show()
        
        # Set initial width
        self.setFixedWidth(self.MINIMIZED_WIDTH)
    
    def add_nav_button(self, text, icon_name, index):
        btn = SidebarButton(text, icon_name, self._dark_mode)
        btn.clicked.connect(lambda: self.handle_button_click(index))
        self.layout.addWidget(btn)
        self.buttons.append(btn)
    
    def handle_button_click(self, index):
        # Uncheck all other buttons
        for btn in self.buttons:
            btn.setChecked(False)
        
        # Check the clicked button
        self.buttons[index].setChecked(True)
        
        # Emit the page change signal
        self.page_changed.emit(index)
    
    def toggle_sidebar(self):
        target_width = self.MINIMIZED_WIDTH if self.expanded else self.EXPANDED_WIDTH
        
        # Create animation
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(200)
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(target_width)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Update button states and layouts
        if self.expanded:
            self.title.hide()
            for btn in self.buttons:
                btn.setText("")
            # Set chevron-right icon with correct color
            icon_color = 'white' if self._dark_mode else 'black'
            self.collapse_btn.setIcon(icon("fa5s.chevron-right", color=icon_color))
            self.collapse_btn_expanded.setIcon(icon("fa5s.chevron-right", color=icon_color))
            # Switch to collapsed layout
            self.expanded_container.hide()
            self.bottom_container.show()
        else:
            # Set chevron-left icon with correct color
            icon_color = 'white' if self._dark_mode else 'black'
            self.collapse_btn.setIcon(icon("fa5s.chevron-left", color=icon_color))
            self.collapse_btn_expanded.setIcon(icon("fa5s.chevron-left", color=icon_color))
            # Switch to expanded layout
            self.bottom_container.hide()
            self.expanded_container.show()
            # Show labels after animation completes
            self.animation.finished.connect(self.show_labels)
        
        self.expanded = not self.expanded
        self.animation.start()
    
    def show_labels(self):
        """Show labels for buttons when sidebar is expanded"""
        self.title.show()
        for i, btn in enumerate(self.buttons):
            btn.setText(self.button_labels[i])

class MainContent(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("mainContent")
    
    def add_widget(self, widget, name):
        self.addWidget(widget)
        widget.setObjectName(f"page_{name.lower()}")
