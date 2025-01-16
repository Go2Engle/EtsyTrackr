from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                              QGridLayout, QSizePolicy, QPushButton, QComboBox, 
                              QTableWidget, QTableWidgetItem, QHeaderView)
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
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(1)
        self.setMidLineWidth(1)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(10)
        title_label.setFont(title_font)
        
        # Value
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_font = QFont()
        value_font.setPointSize(16)
        value_font.setBold(True)
        value_label.setFont(value_font)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        self.setLayout(layout)
        self.value_label = value_label
        self.title_label = title_label
        
    def update_value(self, value, title=None):
        self.value_label.setText(value)
        if title:
            self.title_label.setText(title)

class ChartWidget(QFrame):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout()
        
        # Create matplotlib figure
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        
        # Store current data for theme updates
        self.current_data = None
        self.current_chart_type = None
        self.current_title = None
        self.current_series_names = None
        
        # Connect theme change signal
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.on_theme_changed)
        
        self.update_chart_theme()
    
    def on_theme_changed(self, is_dark):
        # Replot the data with new theme if we have data
        if self.current_data:
            self.plot_data(
                self.current_data,
                self.current_chart_type,
                self.current_title,
                self.current_series_names
            )
    
    def update_chart_theme(self):
        is_dark = self.theme_manager.is_dark_mode() if self.theme_manager else False
        theme = self.theme_manager.get_theme() if self.theme_manager else {}
        
        # Set figure background color
        self.figure.patch.set_facecolor(theme.get('background', '#ffffff'))
        
        # Update all existing axes
        for ax in self.figure.get_axes():
            # Set axis background
            ax.set_facecolor(theme.get('background', '#ffffff'))
            
            # Set text color
            text_color = theme.get('text', '#000000')
            ax.tick_params(colors=text_color)
            ax.xaxis.label.set_color(text_color)
            ax.yaxis.label.set_color(text_color)
            if ax.title:
                ax.title.set_color(text_color)
            
            # Set grid color
            ax.grid(True, linestyle='--', alpha=0.2, color=theme.get('border', '#cccccc'))
            
            # Set spine colors
            for spine in ax.spines.values():
                spine.set_color(theme.get('border', '#cccccc'))
        
        self.canvas.draw()
    
    def plot_data(self, data, chart_type='line', title='', series_names=None):
        # Store current data for theme updates
        self.current_data = data
        self.current_chart_type = chart_type
        self.current_title = title
        self.current_series_names = series_names
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        theme = self.theme_manager.get_theme() if self.theme_manager else {}
        primary_color = theme.get('primary', '#1a73e8')
        
        # Set default axis labels
        ax.set_xlabel('Date')
        ax.set_ylabel('Amount ($)')
        
        # Check for empty data properly
        if (not isinstance(data, dict) or 
            'labels' not in data or 
            'values' not in data or 
            len(data['labels']) == 0 or 
            len(data['values']) == 0):
            # No data to plot, just set up empty chart with labels
            self.figure.subplots_adjust(bottom=0.2)
            if title:
                ax.set_title(title)
            self.update_chart_theme()
            return
        
        if chart_type == 'line':
            if isinstance(data['labels'][0], str):
                dates = [mdates.datestr2num(d) for d in data['labels']]
            else:
                dates = data['labels']
            
            # Plot line with theme color
            ax.plot(dates, data['values'], marker='o', color=primary_color)
            
            if isinstance(data['labels'][0], str):
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            self.figure.subplots_adjust(bottom=0.2)
            
        elif chart_type == 'bar':
            ax.bar(data['labels'], data['values'], color=primary_color)
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            self.figure.subplots_adjust(bottom=0.2)
            
        elif chart_type == 'pie':
            non_zero_values = []
            non_zero_labels = []
            for value, label in zip(data['values'], data['labels']):
                if value > 0:
                    non_zero_values.append(value)
                    non_zero_labels.append(label)
            
            if non_zero_values:
                # Create color variations based on primary color
                colors = [primary_color]
                for i in range(1, len(non_zero_values)):
                    # Adjust brightness for each slice
                    colors.append(f"#{int(primary_color[1:], 16):06x}")
                ax.pie(non_zero_values, labels=non_zero_labels, autopct='%1.1f%%', colors=colors)
        
        elif chart_type == 'stacked_bar':
            if len(data.get('values', [])) == 0:
                return
                
            bottom = np.zeros(len(data['labels']))
            for i, values in enumerate(data['values']):
                if isinstance(values, (list, np.ndarray)) and len(values) > 0:  # Only plot if we have data
                    # Create color variations for each series
                    color = f"#{int(primary_color[1:], 16) + i*0x222222:06x}"
                    ax.bar(data['labels'], values, bottom=bottom,
                          label=series_names[i] if series_names else f'Series {i}',
                          color=color)
                    bottom += values
            
            ax.legend()
            if isinstance(data['labels'][0], str):
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            self.figure.subplots_adjust(bottom=0.2)
        
        if title:
            ax.set_title(title)
        
        self.update_chart_theme()

class DashboardWidget(QWidget):
    def __init__(self, db, theme_manager, sales_page):
        super().__init__()
        self.db = db
        self.theme_manager = theme_manager
        self.init_ui()
        
        # Set default to current month/year
        self.current_month = datetime.now().month
        self.current_year = datetime.now().year
        
        # Connect theme change signal
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.on_theme_changed)
        
        # Initial refresh
        QTimer.singleShot(0, self.refresh_dashboard)
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Create filter controls
        filter_layout = QHBoxLayout()
        
        # Year filter
        self.year_filter = QComboBox()
        current_year = datetime.now().year
        self.year_filter.addItems([str(year) for year in range(current_year, current_year-5, -1)])
        self.year_filter.currentTextChanged.connect(self.refresh_dashboard)
        filter_layout.addWidget(QLabel("Year:"))
        filter_layout.addWidget(self.year_filter)
        
        # Month filter
        self.month_filter = QComboBox()
        self.month_filter.addItems(['All Months'] + list(calendar.month_name)[1:])  # Add 'All Months' option and skip empty first item
        current_month = datetime.now().month
        self.month_filter.setCurrentIndex(current_month)  # Set to current month (index is now offset by 1 due to 'All Months')
        self.month_filter.currentTextChanged.connect(self.refresh_dashboard)
        filter_layout.addWidget(QLabel("Month:"))
        filter_layout.addWidget(self.month_filter)
        
        # Add refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_dashboard)
        filter_layout.addWidget(self.refresh_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Title
        title = QLabel("Dashboard")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Stats Grid
        stats_grid = QGridLayout()
        
        # Create stat cards
        self.total_sales_card = StatCard("Total Sales (30 Days)", "$0.00")
        self.total_orders_card = StatCard("Total Orders (30 Days)", "0")
        self.avg_order_value_card = StatCard("Average Order Value", "$0.00")
        self.total_shipping_card = StatCard("Total Shipping (30 Days)", "$0.00")
        self.total_tax_card = StatCard("Total Tax (30 Days)", "$0.00")
        self.total_fees_card = StatCard("Total Fees (30 Days)", "$0.00")
        self.total_listing_fees_card = StatCard("Total Listing Fees (30 Days)", "$0.00")
        self.net_income_card = StatCard("Net Income (30 Days)", "$0.00")
        self.profit_margin_card = StatCard("Profit Margin", "0%")
        self.total_profit_card = StatCard("Total Profit After Expenses", "$0.00")
        
        # Add cards to grid
        stats_grid.addWidget(self.total_sales_card, 0, 0)
        stats_grid.addWidget(self.total_orders_card, 0, 1)
        stats_grid.addWidget(self.avg_order_value_card, 0, 2)
        stats_grid.addWidget(self.total_shipping_card, 1, 0)
        stats_grid.addWidget(self.total_tax_card, 1, 1)
        stats_grid.addWidget(self.total_fees_card, 1, 2)
        stats_grid.addWidget(self.total_listing_fees_card, 2, 0)
        stats_grid.addWidget(self.net_income_card, 2, 1)
        stats_grid.addWidget(self.profit_margin_card, 2, 2)
        stats_grid.addWidget(self.total_profit_card, 3, 0, 1, 3)  # Span across all columns

        layout.addLayout(stats_grid)
        
        # Charts Grid
        charts_grid = QGridLayout()
        
        # Create chart widgets
        self.sales_chart = ChartWidget(self.theme_manager)
        self.expenses_chart = ChartWidget(self.theme_manager)
        
        # Add charts to grid
        charts_grid.addWidget(self.sales_chart, 0, 0)
        charts_grid.addWidget(self.expenses_chart, 0, 1)
        
        layout.addLayout(charts_grid)
        
        self.setLayout(layout)
        
    def get_filtered_data(self):
        """Get data filtered by the current date selections"""
        try:
            # Get all statement files
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
                
            # Combine all data
            df = pd.concat(all_data, ignore_index=True)
            if df.empty:
                return None
                
            # Ensure we have a date column and convert it
            date_col = None
            for col in df.columns:
                if 'date' in col.lower():
                    date_col = col
                    break
            
            if date_col is None:
                return None
                
            # Convert date column to datetime
            df[date_col] = pd.to_datetime(df[date_col])
            
            # Apply filters
            selected_year = self.year_filter.currentText()
            selected_month = self.month_filter.currentText()
            
            if selected_year != 'All Years':
                year = int(selected_year)
                if selected_month != 'All Months':
                    month = list(calendar.month_name).index(selected_month)
                    start_date = datetime(year, month, 1)
                    if month == 12:
                        end_date = datetime(year + 1, 1, 1)
                    else:
                        end_date = datetime(year, month + 1, 1)
                    df = df[(df[date_col] >= start_date) & (df[date_col] < end_date)]
                else:
                    start_date = datetime(year, 1, 1)
                    end_date = datetime(year + 1, 1, 1)
                    df = df[(df[date_col] >= start_date) & (df[date_col] < end_date)]
            
            # Rename date column to standardized name
            df = df.rename(columns={date_col: 'Date'})
            return df
            
        except Exception:
            return None
            
    def get_date_filter(self):
        """Get start and end dates based on current filter selections"""
        selected_year = self.year_filter.currentText()
        selected_month = self.month_filter.currentText()
        
        now = datetime.now()
        
        # Handle All Years case
        if selected_year == 'All Years':
            return None, None
        
        year = int(selected_year)
        
        # Handle specific month
        if selected_month != 'All Months':
            month = list(calendar.month_name).index(selected_month)
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            return start_date, end_date
        
        # Handle full year when 'All Months' is selected
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        return start_date, end_date

    def reset_metrics(self):
        """Reset all metrics to zero"""
        self.total_sales_card.update_value("$0.00")
        self.total_orders_card.update_value("0")
        self.avg_order_value_card.update_value("$0.00")
        self.total_shipping_card.update_value("$0.00")
        self.total_tax_card.update_value("$0.00")
        self.total_fees_card.update_value("$0.00")
        self.total_listing_fees_card.update_value("$0.00")
        self.net_income_card.update_value("$0.00")
        self.profit_margin_card.update_value("0%")
        self.total_profit_card.update_value("$0.00")
        
        # Reset charts with empty data but proper structure
        empty_data = {'labels': [], 'values': []}
        self.sales_chart.plot_data(empty_data, title='Sales Over Time')
        self.expenses_chart.plot_data(empty_data, title='Expenses Over Time')

    def refresh_dashboard(self):
        """Refresh all dashboard widgets"""
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
        """Update dashboard metrics with new data"""
        try:
            # Calculate basic metrics
            total_sales = df['Sale Amount'].sum()
            total_orders = len(df[df['Sale Amount'] > 0])
            avg_order_value = total_sales / total_orders if total_orders > 0 else 0
            total_shipping = df['Shipping Fee'].sum()
            total_tax = df['Sales Tax'].sum()
            total_fees = df['Item Transaction Fee'].sum() + df['Shipping Transaction Fee'].sum() + df['Processing Fee'].sum()
            total_listing_fees = df['Listing Fee'].sum()
            net_income = total_sales + total_shipping + total_tax + total_fees + total_listing_fees
            profit_margin = (net_income / total_sales * 100) if total_sales > 0 else 0
            
            # Get total expenses for the period
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
            
            # Calculate total profit after expenses
            total_profit = net_income - total_expenses
            
            # Update stat cards
            self.total_sales_card.update_value(f"${total_sales:,.2f}")
            self.total_orders_card.update_value(str(total_orders))
            self.avg_order_value_card.update_value(f"${avg_order_value:,.2f}")
            self.total_shipping_card.update_value(f"${total_shipping:,.2f}")
            self.total_tax_card.update_value(f"${total_tax:,.2f}")
            self.total_fees_card.update_value(f"${total_fees:,.2f}")
            self.total_listing_fees_card.update_value(f"${total_listing_fees:,.2f}")
            self.net_income_card.update_value(f"${net_income:,.2f}")
            self.profit_margin_card.update_value(f"{profit_margin:.1f}%")
            
            # Update total profit card with color based on value
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
        """Update all charts with current data"""
        try:
            # Sales Over Time
            if not df.empty:
                # Convert date strings to datetime objects
                dates = pd.to_datetime(df['Date'])
                
                # Group by date and sum sales
                daily_sales = df.groupby('Date')['Sale Amount'].sum()
                
                # Plot sales data
                self.sales_chart.plot_data({
                    'labels': daily_sales.index,
                    'values': daily_sales.values
                }, chart_type='line', title='Daily Sales')
            
            # Expenses Chart
            start_date, end_date = self.get_date_filter()
            
            # Get Etsy fees
            fees_data = {
                'Date': [],
                'Amount': [],
                'Type': []
            }
            
            if not df.empty:
                # Add Etsy fees
                for _, row in df.iterrows():
                    date = pd.to_datetime(row['Date'])
                    
                    # Transaction fees
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
                        fees_data['Type'].append('Etsy Fees')
            
            # Add expenses from expenses tab
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
                # Convert to DataFrame for easier manipulation
                fees_df = pd.DataFrame(fees_data)
                
                # Group by date and type, then sum amounts
                daily_fees = fees_df.groupby(['Date', 'Type'])['Amount'].sum().unstack(fill_value=0)
                
                # Prepare data for plotting
                plot_data = {
                    'labels': daily_fees.index,
                    'values': [daily_fees['Etsy Fees'].values if 'Etsy Fees' in daily_fees else [],
                             daily_fees['Other Expenses'].values if 'Other Expenses' in daily_fees else []]
                }
                
                # Plot stacked bar chart
                self.expenses_chart.plot_data(plot_data, chart_type='stacked_bar', 
                                           title='Daily Expenses', 
                                           series_names=['Etsy Fees', 'Other Expenses'])
            
        except Exception as e:
            print(f"Error updating charts: {str(e)}")

    def on_theme_changed(self, is_dark):
        # Refresh all charts with current data
        self.refresh_dashboard()
