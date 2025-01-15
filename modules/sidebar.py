from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                              QStackedWidget, QLabel, QFrame, QHBoxLayout)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon
from qtawesome import icon
import os

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
        self.expanded = False
        self.MINIMIZED_WIDTH = 72
        self.EXPANDED_WIDTH = 260
        self.theme_manager = theme_manager
        self._dark_mode = theme_manager.is_dark_mode() if theme_manager else False
        
        if theme_manager:
            theme_manager.theme_changed.connect(self.on_theme_changed)
        
        self.setup_ui()
    
    def on_theme_changed(self, is_dark):
        self._dark_mode = is_dark
        for btn in self.buttons:
            btn.set_dark_mode(is_dark)
        icon_name = "fa5s.chevron-right" if not self.expanded else "fa5s.chevron-left"
        self.collapse_btn.setIcon(icon(icon_name, color='white' if is_dark else 'black'))
    
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
        title_layout.addWidget(self.logo)
        
        # App title
        self.title = QLabel("EtsyTrackr")
        self.title.setObjectName("sidebarTitle")
        self.title.hide()
        title_layout.addWidget(self.title)
        
        title_layout.addStretch()
        self.layout.addLayout(title_layout)
        
        # Add spacing
        self.layout.addSpacing(24)
        
        # Navigation buttons
        self.buttons = []
        self.add_nav_button("Dashboard", "fa5s.chart-line", 0)
        self.add_nav_button("Sales", "fa5s.shopping-cart", 1)
        self.add_nav_button("Expenses", "fa5s.receipt", 2)
        self.add_nav_button("Settings", "fa5s.cog", 3)
        
        # Set first button as active
        if self.buttons:
            self.buttons[0].setChecked(True)
        
        # Hide text initially since we start minimized
        for btn in self.buttons:
            btn.setText("")
        
        # Add stretch to push collapse button to bottom
        self.layout.addStretch()
        
        # Collapse button
        self.collapse_btn = SidebarButton("", "fa5s.chevron-right", self._dark_mode)
        self.collapse_btn.setCheckable(False)
        self.collapse_btn.clicked.connect(self.toggle_sidebar)
        self.layout.addWidget(self.collapse_btn)
        
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
        
        # Update button states
        if self.expanded:
            self.title.hide()
            for btn in self.buttons:
                btn.setText("")
            # Set chevron-right icon with correct color
            self.collapse_btn.setIcon(icon("fa5s.chevron-right", color='white' if self._dark_mode else 'black'))
        else:
            self.animation.finished.connect(lambda: self.show_labels())
            # Set chevron-left icon with correct color
            self.collapse_btn.setIcon(icon("fa5s.chevron-left", color='white' if self._dark_mode else 'black'))
        
        self.animation.start()
        self.expanded = not self.expanded
    
    def show_labels(self):
        self.title.show()
        for i, btn in enumerate(self.buttons):
            labels = ["Dashboard", "Sales", "Expenses", "Settings"]
            btn.setText(labels[i])

class MainContent(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("mainContent")
    
    def add_widget(self, widget, name):
        self.addWidget(widget)
        widget.setObjectName(f"page_{name.lower()}")
