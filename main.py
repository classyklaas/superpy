# Imports
import argparse
import csv
import json
import datetime
import os
import pandas as pd
from halo import Halo
from time import sleep
from rich.console import Console
from pandas import read_csv
from datetime import date
import getpass
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Do not change these lines.
__winc_id__ = 'a2bc36ea784242e4989deb157d527ba0'
__human_name__ = 'superpy'

current_date = datetime.datetime.today().strftime('%Y-%m-%d')
current_date_and_time = datetime.datetime.now()
yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

# First, we're going to set up a couple of argparses. 
def create_parsers():
    parser = argparse.ArgumentParser(
        prog='SuperPy',
        description='A command-line tool used to keep track of inventory',
        epilog='And that\'s how it\'s done!',
        formatter_class=argparse.RawTextHelpFormatter
        )
    #Splitting up functionality by creating a subparser of the main parser right above. 'Dest' is the name of the attribute under which sub-command name will be stored        
    subparsers = parser.add_subparsers(
        dest='command', 
        required=True
        )

    #Parser to be used to advance time by the amount of days given. Example: python main.py --advance_time 2
    advance_time_parser = subparsers.add_parser('advance_time',  help='Used to advance time by given of days')
    advance_time_parser.add_argument('--days', type=int, help='Number of days to advance time by', default='0')

    #parsers used to register which products have been bought by the supermarket, so that they can be added to their inventory. Example: python main.py buy --product-name orange --price 0.8 --expiration-date 2020-01-01
    buy_parser = subparsers.add_parser('buy', help='Register product bought by supermarket')
    buy_parser.add_argument('--product_name', dest='product_name', type=str, help='Name of product bought by supermarket entered as a string. Add an underscore if the name contains spaces', required=True)
    buy_parser.add_argument('--buying_price', dest='buying_price', type=float, help='Insert buying price as a float', required=True)
    buy_parser.add_argument('--expiration_date', dest='expiration_date', type=datetime.date.fromisoformat, help='Insert date as: YYYY-MM-DD', required=True)

    #parsers used to register which producst have been sold by the supermarket, so that they can be removed from their inventory
    sell_parser = subparsers.add_parser('sell', help='Register product sold by supermarket')
    sell_parser.add_argument('--product_name', dest='product_name', type=str, help='Name of product sold by supermarket entered as a string', required=True)
    sell_parser.add_argument('--selling_price', dest='selling_price', type=float, help='Insert selling price as a float', required=True)

    profit_parser = subparsers.add_parser('report profit', help='Get profit of given day. This can be today, yesterday or a given date in YYYY-MM-DD')
    profit_parser.add_argument('--day', type=str, help='Enter date in YYYY-MM-DD')
    profit_parser.add_argument('--today', help='Today\'s profit')
    profit_parser.add_argument('--yesterday', help='Yesterday\'s profit')

    report = subparsers.add_parser("report", help='Reporting revenue and profit over specified time periods')

    daily_revenue_parser = subparsers.add_parser('report_revenue_of_given_day', help='Get revenue of given day')
    daily_revenue_parser.add_argument('--day', type=str, help='Enter date in YYYY-MM-DD. This can by any date.', required = True)

    revenue_parser = subparsers.add_parser('report_revenue_of_time_period', help='Get revenue of given time period between two dates')
    revenue_parser.add_argument('--from_date', type=str, help='Enter the from-date in YYYY-MM-DD', required = True)
    revenue_parser.add_argument('--to_date', type=str, help='Enter the to-date in YYYY-MM-DD', required = True)

    daily_expenses_parser = subparsers.add_parser('report_expenses_of_given_day', help='Get expenses of given day')
    daily_expenses_parser.add_argument('--day', type=str, help='Enter date in YYYY-MM-DD. This can by any date.', required = True)

    expenses_parser = subparsers.add_parser('report_expenses_of_time_period', help='Get expenses of given time period between two dates')
    expenses_parser.add_argument('--from_date', type=str, help='Enter the from-date in YYYY-MM-DD', required = True)
    expenses_parser.add_argument('--to_date', type=str, help='Enter the to-date in YYYY-MM-DD', required = True)

    daily_profit_parser = subparsers.add_parser('report_profit_of_given_day', help='Get profit of given day')
    daily_profit_parser.add_argument('--day', type=str, help='Enter date in YYYY-MM-DD. This can by any date.', required = True)

    profit_parser = subparsers.add_parser('report_profit_of_time_period', help='Get profit of given time period between two dates')
    profit_parser.add_argument('--from_date', type=str, help='Enter the from-date in YYYY-MM-DD', required = True)
    profit_parser.add_argument('--to_date', type=str, help='Enter the to-date in YYYY-MM-DD')

    inventory_parser = subparsers.add_parser('report_inventory', help='Get inventory of given day')
    inventory_parser.add_argument('--day', help='Enter date in YYYY-MM-DD', required = True)
    inventory_parser.add_argument('--today', help='Today\'s inventory', required = True)
    inventory_parser.add_argument('--yesterday', help='Yesterday\'s inventory', required = True)

    send_email_parser = subparsers.add_parser('send_email')
    send_email_parser.add_argument('--email_address_of_receiver', help='What\'s the email address you\'d like to receive an email?', required=True)
    send_email_parser.add_argument('--subject', type=str, required=True)
    send_email_parser.add_argument('--body', type=str, required=True)
    send_email_parser.add_argument('--attachment_to_send', type=str, required=True)

    report_inventory = subparsers.add_parser('get_products_currently_in_inventory')

    number_of_each_product = subparsers.add_parser('get_count_per_product')

    return parser

def create_txt_files():
    """Creating 3 .txt files with a string '1'. This will be incremented and used as id for the existing inventory, newly bought products and sold products.
    The fourth file will contain the current date. This will be used to advance time."""
    if not os.path.exists('unique_ids_for_inventory.txt'):
        first_id = open('unique_ids_for_inventory.txt', mode='w').write('1')
    if not os.path.exists('unique_ids_for_bought_products.txt'):
        first_id = open('unique_ids_for_bought_products.txt', mode='w').write('1') 
    if not os.path.exists('unique_ids_for_sold_products.txt'):
        first_id = open('unique_ids_for_sold_products.txt', mode='w').write('1') 
    if not os.path.exists('starting_point.txt'):
        starting_point = open('starting_point.txt', mode='w').write(current_date)  

def create_all_necessary_csv_files():
    function_to_create_csv_files_if_non_existent('bought.csv', ['id', 'product_name', 'buying_date', 'buying_price', 'expiration_date'])
    function_to_create_csv_files_if_non_existent('sold.csv', ['id', 'product_name', 'selling_date', 'selling_price'])
    function_to_create_csv_files_if_non_existent('inventory.csv', ['id', 'product_name', 'buying_price', 'expiration_date'])

def advance_time(number_of_days_to_advance: int):
    """To be able to advance through time, we first have to know what day the starting point is. This is stored in the file called 'starting_point.txt'."""
    starting_point = get_current_date()
    print('The current date in YYYY-MM-DD is ' + str(starting_point))
    new_date = (datetime.datetime.today() + datetime.timedelta(days=number_of_days_to_advance)).strftime('%Y-%m-%d')
    print('Adding ' + str(number_of_days_to_advance) + ' days to today\'s date, resulting in ' + new_date)
    open('starting_point.txt', mode='w').write(new_date)

def function_to_create_csv_files_if_non_existent(filename, column_names):
    """Creating .csv files with the given data (filename, column_names)"""
    if not os.path.exists(filename):
        with open(filename, mode='a', newline='') as file_alias:
            csv_writer = csv.DictWriter(
                file_alias, delimiter=',', lineterminator='\n', fieldnames=column_names)
            csv_writer.writeheader()

def get_current_date():
    """This function can be used to retrieve the current date in the file called 'starting_point.txt'. The date is written in that file by the function 'create_txt_file_with_date()' """
    with open('starting_point.txt', mode='r') as file_alias:
        lines = file_alias.readlines()
        current_date = datetime.datetime.strptime(lines[0], '%Y-%m-%d').date()
        return current_date    

def send_email(email_address_of_receiver: str, subject: str, body: str, attachment_to_send: str):
    if attachment_to_send != 'bought.csv' and attachment_to_send != 'sold.csv' and attachment_to_send != 'inventory.csv':
        console = Console()
        console.print('You can only send bought.csv, sold.csv or inventory.csv', style = 'red')
        return
    
    port = 465
    smtp_server = 'smtp.gmail.com'
    sender_email = 'tempemailwa@gmail.com'
    receiver_email = email_address_of_receiver
    body = body
    password = getpass.getpass()
    
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email  
    message['Subject'] = subject
    
    message.attach(MIMEText(body, 'plain'))

    filename = attachment_to_send # The file has to be present in the directory this script (main.py) is in.

    with open(filename, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())

    encoders.encode_base64(part)

    part.add_header(
        'Content-Disposition',
        f"attachment; filename= {filename}",
    )

    message.attach(part)
    text = message.as_string()

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        #Easter egg
        with Halo(text='Loading', spinner='dots'):
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, text)
            #Let's take a second or two to look at our amazing easter egg
            sleep(2.00)
            console = Console()
            console.print('\nEmail sent to ' + receiver_email, style = 'green')
            
def get_products_currently_in_inventory():
    data = pd.read_csv('inventory.csv')
    unique_value = data['product_name'].unique()
    print('Overview of products currently in our inventory:')
    print(unique_value)

def get_count_per_product():
    data = pd.read_csv('inventory.csv')
    unique_value = data.value_counts('product_name')
    print('Number of products currently in our inventory:')
    print(unique_value)

def track_bought_products(product_name: str, buying_price: float, expiration_date:str):
    product_name = product_name
    buying_price = buying_price
    expiration_date = expiration_date
    buying_date = get_current_date()
    
    with open('bought.csv', mode='a', newline='') as file_alias:
        new_id = open('unique_ids_for_bought_products.txt', mode='r').read()
        csv_writer = csv.writer(file_alias, delimiter=',', lineterminator='\n')
        
        row = [  
            new_id,          
            product_name,
            buying_date,
            buying_price,
            expiration_date
        ]

        csv_writer.writerow(row)
        open('unique_ids_for_bought_products.txt', mode='w').write(str(int(new_id) + 1))
        
        add_to_inventory(product_name, buying_price, expiration_date)

def add_to_inventory(product_name: str, buying_price: float, expiration_date: str):
    with open('inventory.csv', mode='a', newline='') as inventory:
        new_id_for_each_row = open('unique_ids_for_inventory.txt', mode='r').read()
        csv_writer = csv.writer(inventory, delimiter=',', lineterminator='\n') 
        row = [
            new_id_for_each_row, 
            product_name, 
            buying_price, 
            expiration_date
            ] 
        csv_writer.writerow(row)
        open('unique_ids_for_inventory.txt', mode='w').write(str(int(new_id_for_each_row) + 1))          

def track_sold_products(product_name: str, selling_price: float):
    if not check_if_product_is_in_stock_and_not_expired(product_name):
        console = Console()
        console.print('Life\'s tough sometimes: product not part of the inventory or expired', style = 'red')
        return

    console = Console()
    console.print('Product sold', style = 'green')
    
    id_of_product_to_be_sold = get_product_id(product_name)

    product_name = product_name
    selling_date = get_current_date()
    selling_price = selling_price
    
    with open('sold.csv', mode='a', newline='') as file_alias:
        new_id = open('unique_ids_for_sold_products.txt', mode='r').read()
        csv_writer = csv.writer(file_alias, delimiter=',', lineterminator='\n')
        
        row = [
            new_id,
            product_name,         
            selling_date,
            selling_price
        ]
        csv_writer.writerow(row)
        open('unique_ids_for_sold_products.txt', mode='w').write(str(int(new_id) + 1))

    data = pd.read_csv('inventory.csv')
    data = data[data.id != int(id_of_product_to_be_sold)]
    data = data.to_csv('inventory.csv', index = False)
    print(data)

def check_if_product_is_in_stock_and_not_expired(product_name: str):
    current_date = datetime.datetime.strptime(open('starting_point.txt', 'r').read(), '%Y-%m-%d')
    
    with open('inventory.csv', mode='r') as file_alias:
        reader = csv.reader(file_alias)

        for every_row in reader: 
            if every_row[1] == product_name:
                expiration_date = datetime.datetime.strptime(every_row[3], '%Y-%m-%d')
                if expiration_date > current_date: 
                    return True 
                else: 
                    return False       

def get_product_id(product_name: str):
    with open('inventory.csv', mode='r') as file_alias:
        reader = csv.reader(file_alias)

        for row in reader: 
            if row[1] == product_name:
                return row[0]

def revenue(day):
    """Revenue is the total amount of money received from the supermarket selling her products.
    This data is available in the .csv file sold.csv"""
    
    if day == current_date:
        dataframe = pd.read_csv('sold.csv')
        revenue = dataframe.loc[dataframe['selling_date'] == day, 'selling_price'].sum()
        console = Console()
        console.print('Today\'s revenue: EUR ', end='', style = 'bold cyan')
        console.print(revenue)
    elif day == yesterday:
        dataframe = pd.read_csv('sold.csv')
        revenue = dataframe.loc[dataframe['selling_date'] == day, 'selling_price'].sum()
        console = Console()
        console.print('Yesterday\'s revenue: EUR ', end='', style = 'bold cyan')
        console.print(revenue)
    else:
        dataframe = pd.read_csv('sold.csv')
        revenue = dataframe.loc[dataframe['selling_date'] == day, 'selling_price'].sum()
        console = Console()
        console.print('Revenue: EUR ', end='', style = 'bold cyan')
        console.print(revenue)
    return revenue

def revenue_over_specified_time_period(from_date, to_date):
    dataframe = pd.read_csv('sold.csv')
    revenue_from = dataframe.loc[dataframe['selling_date'] >= from_date, 'selling_price'].sum()
    revenue_to = dataframe.loc[dataframe['selling_date'] >= to_date, 'selling_price'].sum()
    revenue_over_specified_time_period = revenue_from - revenue_to
    console = Console()
    console.print('Revenue over specified time period: EUR ', end='', style = 'bold cyan')
    console.print(revenue_over_specified_time_period)
    return revenue_over_specified_time_period

def expenses(day):
    """Expenses is the total amount received out of the supermarket buying her products.
    This data is available in the .csv file bought.csv"""
    current_date = get_current_date()
    if day == current_date:
        dataframe = pd.read_csv('bought.csv')
        expenses = dataframe.loc[dataframe['buying_date'] == day, 'buying_price'].sum()
        console = Console()
        console.print('Expenses: EUR ', end='', style = 'bold cyan')
        console.print(expenses)
    elif day == yesterday:
        dataframe = pd.read_csv('bought.csv')
        expenses = dataframe.loc[dataframe['buying_date'] == day, 'buying_price'].sum()
        console = Console()
        console.print('Expenses: EUR ', end='', style = 'bold cyan')
        console.print(expenses)
    else:
        dataframe = pd.read_csv('bought.csv')
        expenses = dataframe.loc[dataframe['buying_date'] == day, 'buying_price'].sum()
        console = Console()
        console.print('Expenses: EUR ', end='', style = 'bold cyan')
        console.print(expenses)
    return expenses  

def expenses_over_specified_time_period(from_date, to_date):
    dataframe = pd.read_csv('bought.csv')
    expenses_from = dataframe.loc[dataframe['buying_date'] >= from_date, 'buying_price'].sum()
    expenses_to = dataframe.loc[dataframe['buying_date'] >= to_date, 'buying_price'].sum()
    expenses_over_specified_time_period = expenses_from - expenses_to
    console = Console()
    console.print('Expenses over specified time period: EUR ', end='', style = 'bold cyan')
    console.print(expenses_over_specified_time_period)
    return expenses_over_specified_time_period             

def profit(day):
    """Profit == revenue minus expenses"""
    global revenue, expenses
    revenue = revenue(day)
    expenses = expenses(day)
    profit  = revenue - expenses
    console = Console()
    console.print('Profit: EUR ', end='', style = 'bold cyan')
    console.print(profit)

def profit_over_specified_time_period(from_date, to_date):
    """Profit == revenue minus expenses"""
    revenue = revenue_over_specified_time_period(from_date, to_date)
    expenses = expenses_over_specified_time_period(from_date, to_date)
    profit  = revenue - expenses
    console = Console()
    console.print('Profit over specified time period: EUR ', end='', style = 'bold cyan')
    console.print(profit)

def main():
    create_txt_files()
    create_all_necessary_csv_files()
    parser = create_parsers()
    args = parser.parse_args()
    today = str(get_current_date)

    if args.command == 'get_products_currently_in_inventory':
        get_products_currently_in_inventory()

    if args.command == 'get_count_per_product':
        get_count_per_product()    

    if args.command == 'buy':
        track_bought_products(args.product_name, args.buying_price, args.expiration_date)

    if args.command == 'sell':
        track_sold_products(args.product_name, args.selling_price) 

    if args.command == 'advance_time':
        advance_time(args.days)
        today = str(get_current_date())

    if args.command == 'report_revenue_of_given_day':
        revenue(args.day)

    if args.command == 'report_expenses_of_given_day':
        expenses(args.day)  

    if args.command == 'report_profit_of_given_day':
        profit(args.day) 

    if args.command == 'turn_csv_file_into_json':
        turn_csv_file_into_json(args.csv_file)    

    if args.command == 'send_email':
        send_email(args.email_address_of_receiver, args.subject, args.body, args.attachment_to_send)    

    if args.command == 'report_revenue_of_time_period':
        revenue_over_specified_time_period(args.from_date, args.to_date)
    
    if args.command == 'report_expenses_of_time_period':
        expenses_over_specified_time_period(args.from_date, args.to_date)

    if args.command == 'report_profit_of_time_period':
        profit_over_specified_time_period(args.from_date, args.to_date)

if __name__ == '__main__':
    main()