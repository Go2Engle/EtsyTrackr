import os
import json
import pandas as pd
from datetime import datetime
import shutil

class Database:
    def __init__(self, storage_path):
        self.storage_path = storage_path
        self.expenses_file = os.path.join(storage_path, 'expenses.json')
        self.statements_dir = os.path.join(storage_path, 'statements')
        self.receipts_dir = os.path.join(storage_path, 'receipts')
        
        # Initialize storage files if they don't exist
        self._init_storage()
    
    def _init_storage(self):
        if not os.path.exists(self.expenses_file):
            with open(self.expenses_file, 'w') as f:
                json.dump([], f)
        
        os.makedirs(self.statements_dir, exist_ok=True)
        os.makedirs(self.receipts_dir, exist_ok=True)
    
    def add_expense(self, expense_data):
        """Add an expense to the database
        expense_data should be a dictionary with:
        - date: date string in ISO format
        - description: string
        - amount: float
        - receipt_file: optional string, path to receipt
        """
        with open(self.expenses_file, 'r') as f:
            expenses = json.load(f)
        
        # Find the next available ID
        max_id = max([expense['id'] for expense in expenses]) if expenses else 0
        next_id = max_id + 1
        
        expense = {
            'id': next_id,
            'date': expense_data['date'],
            'description': expense_data['description'],
            'amount': expense_data['amount'],
            'receipt_file': expense_data.get('receipt_file')
        }
        
        expenses.append(expense)
        
        with open(self.expenses_file, 'w') as f:
            json.dump(expenses, f)
        
        return next_id
    
    def get_expenses(self, start_date=None, end_date=None):
        with open(self.expenses_file, 'r') as f:
            expenses = json.load(f)
        
        if start_date and end_date:
            filtered_expenses = [
                exp for exp in expenses 
                if start_date <= datetime.fromisoformat(exp['date']).date() <= end_date
            ]
            return filtered_expenses
        return expenses
    
    def get_existing_order_ids(self):
        """Get a set of all existing Order IDs from processed statements"""
        existing_orders = set()
        
        for filename in os.listdir(self.statements_dir):
            if filename.startswith('processed_') and filename.endswith('.csv'):
                file_path = os.path.join(self.statements_dir, filename)
                try:
                    df = pd.read_csv(file_path)
                    # Add all non-null Order IDs to the set
                    existing_orders.update(str(order_id) for order_id in df['Order ID'].dropna())
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
                    
        return existing_orders
        
    def clean_amount(self, amount_str):
        """Convert currency string to float"""
        if isinstance(amount_str, float):
            return amount_str
        if pd.isna(amount_str) or amount_str == '--':
            return 0.0
        # Remove $ and any spaces, then convert to float
        return float(str(amount_str).replace('$', '').replace(',', '').strip())

    def process_statement_data(self, df):
        """Process statement data to consolidate transactions by Order ID"""
        # Replace '--' with NaN
        df = df.replace('--', pd.NA)
        
        # Try different date formats
        for date_format in ['%d-%b-%y', '%B %d, %Y', '%Y-%m-%d']:
            try:
                df['Date'] = pd.to_datetime(df['Date'], format=date_format)
                break
            except:
                continue
        
        if pd.api.types.is_datetime64_any_dtype(df['Date']) == False:
            print("Failed to parse dates")
            return None
        
        # Initialize order data dictionary
        orders = {}
        
        # First pass: Process sales, refunds, and fees
        for _, row in df.iterrows():
            # Extract order ID from Title or Info if present
            order_id = None
            if 'Order #' in str(row['Title']):
                order_id = row['Title'].split('Order #')[-1].split()[0]
            elif 'Order #' in str(row['Info']):
                order_id = row['Info'].split('Order #')[-1].split()[0]
            
            # Handle listing fees (create new entry)
            if row['Type'] == 'Fee' and ('Listing fee' in str(row['Title']) or 'Credit for listing fee' in str(row['Title'])):
                listing_id = None
                if 'Listing #' in str(row['Info']):
                    listing_id = row['Info'].split('Listing #')[-1].split()[0]
                if listing_id:
                    key = f"Listing_{listing_id}"
                    if key not in orders:
                        orders[key] = {
                            'Date': row['Date'],
                            'Order ID': f"Listing #{listing_id}",
                            'Items': 'Listing Fee',
                            'Sale Amount': 0.0,
                            'Shipping Fee': 0.0,
                            'Sales Tax': 0.0,
                            'Shipping Transaction Fee': 0.0,
                            'Item Transaction Fee': 0.0,
                            'Processing Fee': 0.0,
                            'Listing Fee': 0.0,
                            'Net': 0.0
                        }
                    # Add the fee or credit
                    fee_amount = self.clean_amount(row['Net'])
                    orders[key]['Listing Fee'] += fee_amount
                    orders[key]['Net'] += fee_amount
                continue
            
            # Handle shipping labels (create new entry)
            if row['Type'] == 'Shipping' and 'shipping label' in str(row['Title'].lower()):
                label_id = None
                if 'Label #' in str(row['Info']):
                    label_id = row['Info'].split('Label #')[-1].split()[0]
                if label_id:
                    orders[f"Label_{label_id}"] = {
                        'Date': row['Date'],
                        'Order ID': f"Label #{label_id}",
                        'Items': 'Shipping Label',
                        'Sale Amount': 0.0,
                        'Shipping Fee': self.clean_amount(row['Net']),
                        'Sales Tax': 0.0,
                        'Shipping Transaction Fee': 0.0,
                        'Item Transaction Fee': 0.0,
                        'Processing Fee': 0.0,
                        'Listing Fee': 0.0,
                        'Net': self.clean_amount(row['Net'])
                    }
                continue
            
            # Initialize order if not exists (for regular transactions)
            if order_id and order_id not in orders:
                orders[order_id] = {
                    'Date': row['Date'],
                    'Order ID': order_id,
                    'Items': '',
                    'Sale Amount': 0.0,
                    'Shipping Fee': 0.0,
                    'Sales Tax': 0.0,
                    'Shipping Transaction Fee': 0.0,
                    'Item Transaction Fee': 0.0,
                    'Processing Fee': 0.0,
                    'Listing Fee': 0.0,
                    'Net': 0.0
                }
            
            # Handle different transaction types
            if order_id:
                if row['Type'] == 'Sale':
                    amount = self.clean_amount(row['Amount'])
                    orders[order_id]['Sale Amount'] = amount
                    orders[order_id]['Net'] = amount
                
                elif row['Type'] == 'Refund':
                    amount = self.clean_amount(row['Amount'])
                    orders[order_id]['Sale Amount'] = amount  # This will be negative
                    orders[order_id]['Net'] = amount
                    # Mark the items as refunded
                    if orders[order_id]['Items']:
                        orders[order_id]['Items'] = '[REFUNDED] ' + orders[order_id]['Items']
                    else:
                        orders[order_id]['Items'] = '[REFUNDED] Order'
                
                elif row['Type'] == 'Fee':
                    fee_amount = self.clean_amount(row['Net'])
                    if 'Transaction fee: Shipping' in row['Title'] or 'Credit for transaction fee on shipping' in row['Title']:
                        orders[order_id]['Shipping Transaction Fee'] += fee_amount
                        orders[order_id]['Net'] += fee_amount
                    elif 'Transaction fee:' in row['Title'] or 'Credit for transaction fee on' in row['Title']:
                        orders[order_id]['Item Transaction Fee'] += fee_amount
                        orders[order_id]['Net'] += fee_amount
                        # Extract item name from transaction fee if not already set
                        if not orders[order_id]['Items']:
                            if 'Transaction fee:' in row['Title']:
                                item_name = row['Title'].split('Transaction fee:')[-1].strip()
                            else:
                                item_name = row['Title'].split('Credit for transaction fee on')[-1].strip()
                            if item_name:
                                orders[order_id]['Items'] = item_name
                    elif 'Processing fee' in row['Title'] or 'Credit for processing fee' in row['Title']:
                        orders[order_id]['Processing Fee'] += fee_amount
                        orders[order_id]['Net'] += fee_amount
                
                elif row['Type'] == 'Tax':
                    tax_amount = self.clean_amount(row['Net'])
                    if 'Sales tax paid by buyer' in row['Title'] or 'Refund to buyer for sales tax' in row['Title']:
                        orders[order_id]['Sales Tax'] += tax_amount
                        orders[order_id]['Net'] += tax_amount
        
        # Convert orders to DataFrame
        orders_list = list(orders.values())
        result_df = pd.DataFrame(orders_list)
        
        # Sort by date
        result_df = result_df.sort_values('Date', ascending=False)
        
        return result_df

    def import_etsy_statement(self, file_path):
        """Import an Etsy CSV statement file, skipping duplicate orders"""
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Process the data
            processed_df = self.process_statement_data(df)
            if processed_df is None:
                return False
            
            # Get the month and year from the first date
            first_date = processed_df['Date'].iloc[0]
            month_year = first_date.strftime('%Y-%m')
            
            # Create processed filename
            filename = f'processed_{month_year}.csv'
            output_path = os.path.join(self.statements_dir, filename)
            
            # Save processed data
            processed_df.to_csv(output_path, index=False)
            
            return True
            
        except Exception as e:
            print(f"Error importing statement: {e}")
            return False
            
    def clear_sales_data(self):
        """Clear all sales data by removing processed statement files"""
        try:
            # Remove all processed statement files
            for filename in os.listdir(self.statements_dir):
                if filename.startswith('processed_') and filename.endswith('.csv'):
                    file_path = os.path.join(self.statements_dir, filename)
                    os.remove(file_path)
            return True
        except Exception as e:
            print(f"Error clearing sales data: {e}")
            return False
    
    def get_statements_summary(self, start_date=None, end_date=None):
        """Get aggregated summary of all statements within date range"""
        all_data = []
        
        # Read all processed statement files
        for filename in os.listdir(self.statements_dir):
            if filename.startswith('processed_') and filename.endswith('.csv'):
                file_path = os.path.join(self.statements_dir, filename)
                try:
                    df = pd.read_csv(file_path)
                    
                    # Convert date column
                    df['Date'] = pd.to_datetime(df['Date'])
                    
                    # Filter by date range if specified
                    if start_date and end_date:
                        mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
                        df = df[mask]
                    
                    if not df.empty:
                        all_data.append(df)
                        
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
                    continue
        
        if not all_data:
            return None
            
        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Sort by date
        combined_df = combined_df.sort_values('Date', ascending=False)
        
        return combined_df
    
    def update_storage_location(self, new_path):
        """Update the storage location and move all files to the new location"""
        if not os.path.exists(new_path):
            os.makedirs(new_path)
        
        # Move expenses file
        new_expenses_file = os.path.join(new_path, 'expenses.json')
        if os.path.exists(self.expenses_file):
            with open(self.expenses_file, 'r') as f:
                expenses_data = json.load(f)
            with open(new_expenses_file, 'w') as f:
                json.dump(expenses_data, f)
        
        # Create new directories
        new_statements_dir = os.path.join(new_path, 'statements')
        new_receipts_dir = os.path.join(new_path, 'receipts')
        os.makedirs(new_statements_dir, exist_ok=True)
        os.makedirs(new_receipts_dir, exist_ok=True)
        
        # Update paths
        self.storage_path = new_path
        self.expenses_file = new_expenses_file
        self.statements_dir = new_statements_dir
        self.receipts_dir = new_receipts_dir
    
    def update_expense_receipt(self, expense_id, receipt_file):
        """Update the receipt file for an existing expense"""
        with open(self.expenses_file, 'r') as f:
            expenses = json.load(f)
        
        # Find and update the expense
        for expense in expenses:
            if expense['id'] == expense_id:
                expense['receipt_file'] = receipt_file
                break
        
        # Save updated expenses
        with open(self.expenses_file, 'w') as f:
            json.dump(expenses, f)

    def update_expense(self, expense_id, receipt_path=None):
        """Update an expense's receipt path in the database"""
        try:
            with open(self.expenses_file, 'r') as f:
                expenses = json.load(f)
            
            if receipt_path:
                for expense in expenses:
                    if expense['id'] == expense_id:
                        # Store receipt path directly as string
                        expense['receipt_file'] = receipt_path
                        break
            
            with open(self.expenses_file, 'w') as f:
                json.dump(expenses, f)
            
            return True
        except Exception as e:
            print(f"Error updating expense: {str(e)}")
            return False

    def delete_expense(self, expense_id):
        """Delete an expense and its associated receipt file if it exists"""
        try:
            # Load current expenses
            expenses = self.get_expenses()
            
            # Find the expense to delete
            expense_to_delete = None
            remaining_expenses = []
            
            for expense in expenses:
                if expense['id'] == expense_id:
                    expense_to_delete = expense
                else:
                    remaining_expenses.append(expense)
            
            if expense_to_delete is None:
                raise ValueError(f"Expense with ID {expense_id} not found")
            
            # Delete associated receipt file if it exists
            if expense_to_delete.get('receipt_file'):
                receipt_path = os.path.join(self.receipts_dir, expense_to_delete['receipt_file'])
                if os.path.exists(receipt_path):
                    os.remove(receipt_path)
            
            # Save updated expenses list
            with open(self.expenses_file, 'w') as f:
                json.dump(remaining_expenses, f, indent=4)
            
        except Exception as e:
            raise Exception(f"Failed to delete expense: {str(e)}")
