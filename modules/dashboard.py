from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                              QGridLayout, QSizePolicy, QPushButton, QComboBox, 
                              QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor
import pandas as pd
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import numpy as np
import calendar

class StatCard(QFrame):
    def __init__(self, title, value, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        self.theme_manager = parent.theme_manager if hasattr(parent, 'theme_manager') else None
        
        # Set initial style
        self.update_style()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)  # Reduced spacing between title and value
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(10)
        title_label.setFont(title_font)
        title_label.setWordWrap(True)
        
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_font = QFont()
        value_font.setPointSize(16)
        value_font.setBold(True)
        value_label.setFont(value_font)
        
        # Add stretches for vertical centering
        layout.addStretch()
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addStretch()
        
        self.setLayout(layout)
        self.value_label = value_label
        self.title_label = title_label
        
        # Set fixed height and minimum width
        self.setFixedHeight(100)
        self.setMinimumWidth(120)
        
        # Set minimum size for the card
        # self.setMinimumSize(120, 100)
        
        # Connect theme change signal if theme manager exists
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.update_style)
    
    def update_style(self):
        theme = self.theme_manager.get_theme() if self.theme_manager else {}
        bg_color = "#2d2d2d" if self.theme_manager and self.theme_manager.is_dark_mode() else "#f5f5f5"
        text_color = "#ffffff" if self.theme_manager and self.theme_manager.is_dark_mode() else "#000000"
        
        self.setStyleSheet(f"""
            StatCard {{
                background-color: {bg_color};
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }}
            QLabel {{
                background-color: transparent;
                border: none;
                color: {text_color};
            }}
        """)
    
    def update_value(self, value, title=None):
        self.value_label.setText(value)
        if title:
            self.title_label.setText(title)

class ChartWidget(QFrame):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setFrameStyle(QFrame.NoFrame)  # Remove frame
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(450)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        
        self.current_data = None
        self.current_chart_type = None
        self.current_title = None
        self.current_series_names = None
        
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.on_theme_changed)
        
        self.update_chart_theme()
    
    def on_theme_changed(self, is_dark):
        self.update_chart_theme()
        # Remove background color setting
        self.update_chart_theme()
        
    def update_chart_theme(self):
        if not self.theme_manager:
            return
            
        theme = self.theme_manager.get_theme()
        bg_color = theme.get('background', '#f5f5f5')
        text_color = theme.get('text', '#000000')
        border_color = theme.get('border', '#cccccc')
        primary_color = theme.get('primary', '#1a73e8')
        
        try:
            # Set figure background
            self.figure.patch.set_facecolor(bg_color)
            
            for ax in self.figure.axes:
                # Set axis background
                ax.set_facecolor(bg_color)
                
                # Set text colors
                ax.tick_params(colors=text_color)
                ax.xaxis.label.set_color(text_color)
                ax.yaxis.label.set_color(text_color)
                if ax.get_title():
                    ax.title.set_color(text_color)
                
                # Set spine colors
                for spine in ax.spines.values():
                    spine.set_color(border_color)
                    
                # Update line colors if there are any lines
                for line in ax.get_lines():
                    line.set_color(primary_color)
            
            self.canvas.draw()
        except Exception as e:
            print(f"Warning: Error updating chart theme: {str(e)}")
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_data is not None:
            self.plot_data(self.current_data, self.current_chart_type, 
                          self.current_title, self.current_series_names)
    
    def plot_data(self, data, chart_type='line', title='', series_names=None):
        self.current_data = data
        self.current_chart_type = chart_type
        self.current_title = title
        self.current_series_names = series_names
        
        self.figure.clear()
        
        # Calculate margins based on widget size
        height = self.height() / self.figure.dpi
        bottom_margin = min(0.35, max(0.3, 60/height))   # Increased bottom margin
        top_margin = min(0.15, max(0.1, 30/height))      # Keep same top margin
        
        self.figure.subplots_adjust(
            bottom=bottom_margin,
            top=1.0 - top_margin,
            left=0.12,
            right=0.95
        )
        
        ax = self.figure.add_subplot(111)
        
        theme = self.theme_manager.get_theme() if self.theme_manager else {}
        primary_color = theme.get('primary', '#1a73e8')
        bg_color = theme.get('background', '#f5f5f5')
        
        # Set background colors
        self.figure.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Amount ($)')
        
        if (not isinstance(data, dict) or 
            'labels' not in data or 
            'values' not in data or 
            len(data['labels']) == 0 or 
            len(data['values']) == 0):
            if title:
                ax.set_title(title)
            self.update_chart_theme()
            return
        
        if chart_type == 'line':
            if isinstance(data['labels'][0], str):
                dates = [mdates.datestr2num(d) for d in data['labels']]
            else:
                dates = data['labels']
            
            ax.plot(dates, data['values'], marker='o', color=primary_color)
            
            if isinstance(data['labels'][0], str):
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            
        elif chart_type == 'bar':
            ax.bar(data['labels'], data['values'], color=primary_color)
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            
        elif chart_type == 'pie':
            non_zero_values = []
            non_zero_labels = []
            for value, label in zip(data['values'], data['labels']):
                if value > 0:
                    non_zero_values.append(value)
                    non_zero_labels.append(label)
            
            if non_zero_values:
                colors = [primary_color]
                for i in range(1, len(non_zero_values)):
                    colors.append(f"#{int(primary_color[1:], 16):06x}")
                ax.pie(non_zero_values, labels=non_zero_labels, autopct='%1.1f%%', colors=colors)
        
        elif chart_type == 'stacked_bar':
            if len(data.get('values', [])) == 0:
                return
                
            bottom = np.zeros(len(data['labels']))
            colors = ['#1a73e8', '#34a853', '#fbbc04', '#ea4335', '#46bdc6']  # Fixed color palette
            
            for i, values in enumerate(data['values']):
                if isinstance(values, (list, np.ndarray)) and len(values) > 0:
                    color = colors[i % len(colors)]  # Cycle through colors
                    ax.bar(data['labels'], values, bottom=bottom,
                          label=series_names[i] if series_names else f'Series {i}',
                          color=color)
                    bottom += values
            
            ax.legend()
            if isinstance(data['labels'][0], str):
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        if title:
            ax.set_title(title)
        
        self.update_chart_theme()

class DashboardWidget(QWidget):
    def __init__(self, db, theme_manager, sales_page):
        super().__init__()
        self.db = db
        self.theme_manager = theme_manager
        self.init_ui()
        
        self.current_month = datetime.now().month
        self.current_year = datetime.now().year
        
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.on_theme_changed)
        
        QTimer.singleShot(0, self.refresh_dashboard)
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)  # Reduced overall spacing
        
        # Add filter section at the top (outside scroll area)
        filter_layout = QHBoxLayout()
        
        self.year_filter = QComboBox()
        years = self.db.get_all_years()  # Get years from both sales and expenses
        if not years:  # If no data, just show current year
            years = [datetime.now().year]
        self.year_filter.addItems(['All Years'] + [str(year) for year in years])
        self.year_filter.setCurrentText(str(datetime.now().year))
        self.year_filter.currentTextChanged.connect(self.on_year_changed)
        filter_layout.addWidget(QLabel("Year:"))
        filter_layout.addWidget(self.year_filter)
        
        self.month_filter = QComboBox()
        current_month = datetime.now().month
        self.month_filter.addItems(['All Months'] + list(calendar.month_name)[1:])
        self.month_filter.setCurrentText(calendar.month_name[current_month])
        self.month_filter.currentTextChanged.connect(self.refresh_dashboard)
        filter_layout.addWidget(QLabel("Month:"))
        filter_layout.addWidget(self.month_filter)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_dashboard)
        filter_layout.addWidget(self.refresh_btn)
        
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)
        
        title = QLabel("Dashboard")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)  # Remove border
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Style the scrollbar
        scroll_area.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #888888;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666666;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # Create container widget for scroll area
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(10)  # Reduced spacing
        scroll_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        
        # Stats container
        stats_container = QVBoxLayout()
        stats_container.setSpacing(10)  # Reduced spacing between rows
        
        # First row - Sales metrics
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(10)
        self.total_sales_card = StatCard("Total Sales", "$0.00", self)
        self.total_orders_card = StatCard("Total Orders", "0", self)
        self.avg_order_value_card = StatCard("Avg Order Value", "$0.00", self)
        row1_layout.addWidget(self.total_sales_card)
        row1_layout.addWidget(self.total_orders_card)
        row1_layout.addWidget(self.avg_order_value_card)
        stats_container.addLayout(row1_layout)
        
        # Second row - Basic fees
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(10)
        self.total_shipping_card = StatCard("Total Shipping", "$0.00", self)
        self.total_tax_card = StatCard("Total Tax", "$0.00", self)
        self.total_fees_card = StatCard("Total Fees", "$0.00", self)
        row2_layout.addWidget(self.total_shipping_card)
        row2_layout.addWidget(self.total_tax_card)
        row2_layout.addWidget(self.total_fees_card)
        stats_container.addLayout(row2_layout)
        
        # Third row - Additional fees
        row3_layout = QHBoxLayout()
        row3_layout.setSpacing(10)
        self.total_listing_fees_card = StatCard("Total Listing Fees", "$0.00", self)
        self.offsite_ads_card = StatCard("Total Offsite Ads", "$0.00", self)
        self.etsy_ads_card = StatCard("Total Etsy Ads", "$0.00", self)
        row3_layout.addWidget(self.total_listing_fees_card)
        row3_layout.addWidget(self.offsite_ads_card)
        row3_layout.addWidget(self.etsy_ads_card)
        stats_container.addLayout(row3_layout)
        
        # Fourth row - Profit metrics
        row4_layout = QHBoxLayout()
        row4_layout.setSpacing(10)
        self.net_income_card = StatCard("Net Income", "$0.00", self)
        self.profit_margin_card = StatCard("Profit Margin", "0%", self)
        self.total_profit_card = StatCard("Total Profit After Expenses", "$0.00", self)
        row4_layout.addWidget(self.net_income_card)
        row4_layout.addWidget(self.profit_margin_card)
        row4_layout.addWidget(self.total_profit_card)
        stats_container.addLayout(row4_layout)
        
        scroll_layout.addLayout(stats_container)
        
        # Charts section
        charts_grid = QGridLayout()
        charts_grid.setSpacing(20)
        
        self.sales_chart = ChartWidget(self.theme_manager)
        self.expenses_chart = ChartWidget(self.theme_manager)
        
        charts_grid.addWidget(self.sales_chart, 0, 0)
        charts_grid.addWidget(self.expenses_chart, 0, 1)
        
        scroll_layout.addLayout(charts_grid)
        
        # Set the scroll widget and add to main layout
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
        
    def get_filtered_data(self):
        try:
            all_data = []
            for filename in os.listdir(self.db.statements_dir):
                if not filename.endswith('.csv'):
                    continue
                    
                file_path = os.path.join(self.db.statements_dir, filename)
                try:
                    df = pd.read_csv(file_path)
                    processed_df = self.db.process_statement_data(df)
                    if processed_df is not None:
                        all_data.append(processed_df)
                except Exception as e:
                    continue
                    
            if not all_data:
                return None
                
            df = pd.concat(all_data, ignore_index=True)
            if df.empty:
                return None
                
            # Convert date column to datetime
            df['Date'] = pd.to_datetime(df['Date'])
            
            # Apply year filter if not 'All Years'
            selected_year = self.year_filter.currentText()
            if selected_year != 'All Years':
                df = df[df['Date'].dt.year == int(selected_year)]
            
            # Apply month filter if not 'All Months'
            selected_month = self.month_filter.currentText()
            if selected_month != 'All Months':
                month_num = list(calendar.month_name).index(selected_month)
                df = df[df['Date'].dt.month == month_num]
            
            if df.empty:
                return None
                
            return df
            
        except Exception as e:
            print(f"Error getting filtered data: {str(e)}")
            return None

    def get_date_filter(self):
        selected_year = self.year_filter.currentText()
        selected_month = self.month_filter.currentText()
        
        now = datetime.now()
        
        if selected_year == 'All Years':
            return None, None
        
        year = int(selected_year)
        
        if selected_month != 'All Months':
            month = list(calendar.month_name).index(selected_month)
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            return start_date, end_date
        
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        return start_date, end_date

    def reset_metrics(self):
        self.total_sales_card.update_value("$0.00")
        self.total_orders_card.update_value("0")
        self.avg_order_value_card.update_value("$0.00")
        self.total_shipping_card.update_value("$0.00")
        self.total_tax_card.update_value("$0.00")
        self.total_fees_card.update_value("$0.00")
        self.total_listing_fees_card.update_value("$0.00")
        self.offsite_ads_card.update_value("$0.00")
        self.etsy_ads_card.update_value("$0.00")
        self.net_income_card.update_value("$0.00")
        self.profit_margin_card.update_value("0%")
        self.total_profit_card.update_value("$0.00")
        
        empty_data = {'labels': [], 'values': []}
        self.sales_chart.plot_data(empty_data, title='Sales Over Time')
        self.expenses_chart.plot_data(empty_data, title='Expenses Over Time')

    def refresh_dashboard(self):
        try:
            df = self.get_filtered_data()
            if df is None or df.empty:
                self.reset_metrics()
                return
            
            self.update_metrics(df)
            self.update_charts(df)
            
        except Exception:
            self.reset_metrics()

    def update_metrics(self, df):
        try:
            total_sales = df['Sale Amount'].sum()
            total_orders = len(df[df['Sale Amount'] > 0])
            avg_order_value = total_sales / total_orders if total_orders > 0 else 0
            total_shipping = df['Shipping Fee'].sum()
            total_tax = df['Sales Tax'].sum()
            total_fees = df['Item Transaction Fee'].sum() + df['Shipping Transaction Fee'].sum() + df['Processing Fee'].sum()
            total_listing_fees = df['Listing Fee'].sum()
            total_offsite_ads = df['Offsite Ads Fee'].sum()
            total_etsy_ads = df['Etsy Ads Fee'].sum()
            net_income = total_sales + total_shipping + total_tax + total_fees + total_listing_fees + total_offsite_ads + total_etsy_ads
            
            
            start_date, end_date = self.get_date_filter()
            
            expenses = self.db.get_expenses()
            total_expenses = 0
            
            if expenses:
                for expense in expenses:
                    expense_date = datetime.strptime(expense['date'], '%Y-%m-%d')
                    if start_date and end_date:
                        if start_date <= expense_date <= end_date:
                            total_expenses += float(expense['amount'])
                    else:
                        total_expenses += float(expense['amount'])
            
            total_profit = net_income - total_expenses
            profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0

            self.total_sales_card.update_value(f"${total_sales:,.2f}")
            self.total_orders_card.update_value(str(total_orders))
            self.avg_order_value_card.update_value(f"${avg_order_value:,.2f}")
            self.total_shipping_card.update_value(f"${abs(total_shipping):,.2f}")
            self.total_tax_card.update_value(f"${abs(total_tax):,.2f}")
            self.total_fees_card.update_value(f"${abs(total_fees):,.2f}")
            self.total_listing_fees_card.update_value(f"${abs(total_listing_fees):,.2f}")
            self.offsite_ads_card.update_value(f"${abs(total_offsite_ads):,.2f}")
            self.etsy_ads_card.update_value(f"${abs(total_etsy_ads):,.2f}")
            self.net_income_card.update_value(f"${net_income:,.2f}")
            self.profit_margin_card.update_value(f"{profit_margin:.1f}%")
            
            profit_text = f"${total_profit:,.2f}"
            self.total_profit_card.update_value(profit_text)
            if total_profit < 0:
                self.total_profit_card.value_label.setStyleSheet("color: red;")
            elif total_profit > 0:
                self.total_profit_card.value_label.setStyleSheet("color: green;")
            else:
                self.total_profit_card.value_label.setStyleSheet("")
            
        except Exception as e:
            print(f"Error updating metrics: {str(e)}")

    def update_charts(self, df):
        try:
            if not df.empty:
                dates = pd.to_datetime(df['Date'])
                
                daily_sales = df.groupby('Date')['Sale Amount'].sum()
                
                self.sales_chart.plot_data({
                    'labels': daily_sales.index,
                    'values': daily_sales.values
                }, chart_type='line', title='Daily Sales')
            
            start_date, end_date = self.get_date_filter()
            
            fees_data = {
                'Date': [],
                'Amount': [],
                'Type': []
            }
            
            if not df.empty:
                for _, row in df.iterrows():
                    date = pd.to_datetime(row['Date'])
                    
                    if row['Item Transaction Fee'] != 0:
                        fees_data['Date'].append(date)
                        fees_data['Amount'].append(abs(row['Item Transaction Fee']))
                        fees_data['Type'].append('Etsy Fees')
                    
                    if row['Shipping Transaction Fee'] != 0:
                        fees_data['Date'].append(date)
                        fees_data['Amount'].append(abs(row['Shipping Transaction Fee']))
                        fees_data['Type'].append('Etsy Fees')
                    
                    if row['Processing Fee'] != 0:
                        fees_data['Date'].append(date)
                        fees_data['Amount'].append(abs(row['Processing Fee']))
                        fees_data['Type'].append('Etsy Fees')
                    
                    if row['Listing Fee'] != 0:
                        fees_data['Date'].append(date)
                        fees_data['Amount'].append(abs(row['Listing Fee']))
                        fees_data['Type'].append('Listing Fees')
                        
                    if row['Offsite Ads Fee'] != 0:
                        fees_data['Date'].append(date)
                        fees_data['Amount'].append(abs(row['Offsite Ads Fee']))
                        fees_data['Type'].append('Offsite Ads')
                        
                    if row['Etsy Ads Fee'] != 0:
                        fees_data['Date'].append(date)
                        fees_data['Amount'].append(abs(row['Etsy Ads Fee']))
                        fees_data['Type'].append('Etsy Ads')
            
            expenses = self.db.get_expenses()
            if expenses:
                for expense in expenses:
                    expense_date = datetime.strptime(expense['date'], '%Y-%m-%d')
                    if start_date and end_date:
                        if start_date <= expense_date <= end_date:
                            fees_data['Date'].append(expense_date)
                            fees_data['Amount'].append(float(expense['amount']))
                            fees_data['Type'].append('Other Expenses')
                    else:
                        fees_data['Date'].append(expense_date)
                        fees_data['Amount'].append(float(expense['amount']))
                        fees_data['Type'].append('Other Expenses')
            
            if fees_data['Date']:
                fees_df = pd.DataFrame(fees_data)
                
                daily_fees = fees_df.groupby(['Date', 'Type'])['Amount'].sum().unstack(fill_value=0)
                
                plot_data = {
                    'labels': daily_fees.index,
                    'values': [daily_fees['Etsy Fees'].values if 'Etsy Fees' in daily_fees else [],
                             daily_fees['Listing Fees'].values if 'Listing Fees' in daily_fees else [],
                             daily_fees['Offsite Ads'].values if 'Offsite Ads' in daily_fees else [],
                             daily_fees['Etsy Ads'].values if 'Etsy Ads' in daily_fees else [],
                             daily_fees['Other Expenses'].values if 'Other Expenses' in daily_fees else []]
                }
                
                self.expenses_chart.plot_data(plot_data, chart_type='stacked_bar', 
                                           title='Daily Expenses', 
                                           series_names=['Etsy Fees', 'Listing Fees', 'Offsite Ads', 'Etsy Ads', 'Other Expenses'])
            
        except Exception as e:
            print(f"Error updating charts: {str(e)}")

    def on_year_changed(self, selected_year):
        """Handle year selection changes"""
        if selected_year == 'All Years':
            self.month_filter.setCurrentText('All Months')
            self.month_filter.setEnabled(False)
        else:
            self.month_filter.setEnabled(True)
        self.refresh_dashboard()

    def on_theme_changed(self, is_dark):
        self.refresh_dashboard()
