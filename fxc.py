import pandas as pd
import colorama
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
import os
from decimal import Decimal
import requests
import json

colorama.init()
pd.options.display.max_columns = None

URL = "https://openexchangerates.org/api/latest.json?app_id=YOUR_API_KEY"
response = requests.get(URL)
data = json.loads(response.text)
currencies = list(data['rates'].keys())
currencies = [x for x in currencies if x[0] != 'X']


def get_exchange_rate(base_currency, quote_currency):
    """_summary_

    Args:
        base_currency (string): left currency
        quote_currency (string): right currency

    Returns:
        float: exchange rate
    """
    exchange_rate = data['rates'][quote_currency] / data['rates'][base_currency]
    return exchange_rate


def calculate_profit_loss(pair, entry_price, exit_price, lot_size):
    """_summary_

    Args:
        pair (string): fx pair or metal such as 'XAU'
        entry_price (float): entry price
        exit_price (float): exit price
        lot_size (float): lot size

    Returns:
        float: profit or loose
    """
    base_currency = pair[:3]
    quote_currency = pair[3:]

    if base_currency in currencies:
        price_difference = Decimal(exit_price) - Decimal(entry_price)
        profit_loss = Decimal(price_difference) * Decimal(lot_size)
        if base_currency == quote_currency:
            return profit_loss
        else:
            exchange_rate = get_exchange_rate(base_currency, quote_currency)
            profit_loss_in_quote_currency = Decimal(profit_loss) * Decimal(exchange_rate)
            return profit_loss_in_quote_currency
    else:
        price_difference = Decimal(exit_price) - Decimal(entry_price)
        profit_loss = Decimal(price_difference) * Decimal(lot_size)
        return profit_loss


def calculate_margin_required(lot_size, contract_size, price, levarage):
    """_summary_

    Args:
        lot_size (float): lot size
        contract_size (int): contract size
        price (float): price

    Returns:
        _type_: _description_
    """
    return (Decimal(lot_size) * Decimal(contract_size) * Decimal(price)) / levarage


def fibonacci(n, lot_size=0.01):
    """_summary_

    Args:
        n (int): nth elemrnt of fibo
         lot_size (float, optional): lot size. Defaults to 0.01.

    Returns:
        list: list of fibo values
    """
    if n < 1:
        return []
    fib_numbers = [0, 1]

    while len(fib_numbers) < n:
        fib_numbers.append(fib_numbers[-1] + fib_numbers[-2])
    fib_numbers = [lot_size * x for x in fib_numbers]
    return fib_numbers[1:]


def swap(pair, swap_rate, days=1, ticket_size=1, lot_size=1):
    """Calculates swap values

    Args:
        pair (string): fx pair or metal such as 'XAU'
        swap_rate (float): swap rate from mt
        days (int, optional): days spent on trade. Defaults to 1.
        ticket_size (int, optional): ticket size for calculating 3 days swap. Defaults to 1.
        lot_size (float, optional): lot size. Defaults to 0.01.

    Returns:
        float: swap walue
    """
    result = days * Decimal(lot_size) * Decimal(swap_rate) * Decimal(ticket_size)

    base_currency = pair[:3]
    quote_currency = pair[3:]

    if base_currency in currencies:
        if base_currency == quote_currency:
            return result
        else:
            exchange_rate = get_exchange_rate(base_currency, quote_currency)
            result_in_quote_currency = Decimal(result) * Decimal(exchange_rate)
            exchange_rate_account_currency = get_exchange_rate(quote_currency, 'USD')
            result_in_account_currency = Decimal(result_in_quote_currency) * Decimal(exchange_rate_account_currency)
            return result_in_account_currency
    else:
        return result


def send_mail(output_file_path, PASSWORD):
    """The func generates an email and sends it to the user with an attachment

    Args:
        output_file_path (str): the path of the file to be attached
        PASSWORD (str): Outlook password
    """
    msg = MIMEMultipart()
    msg['From'] = "your@mail
    msg['To'] = "to@mail"
    msg['Subject'] = "FX game plan for " + pair

    with open(output_file_path, 'rb') as f:
        attachment = MIMEBase('application', "octet-stream")
        attachment.set_payload((f).read())
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment', filename=output_file_path)
    msg.attach(attachment)

    server = smtplib.SMTP('smtp.office365.com', 587)
    server.starttls()
    server.login("your@mail", PASSWORD)
    server.send_message(msg)
    server.quit()


if __name__ == "__main__":
    """ Initial settings """
    while True:
        PASSWORD = os.environ.get('ZPASS')
        is_custom_value = input("Do You want to provide custom lot size values Y/N?: ").upper()
        minimum_price_increment = 0.0001
        fib_lst = fibonacci(15)

        if is_custom_value != "Y":
            start_point = int(input("Fibo start position: "))

        """ Main """
        pair = input("Pair: ").upper()
        contract_size = int(input("Contract Size: "))
        levarage = int(input("Levarage: "))
        swap_rate = Decimal(input("Provide swap rate: "))
        stop_price = Decimal(input("Stop price: "))
        swap_value_daily = swap(pair, swap_rate)
        account_currency = 'USD'
        res_currency = pair[3:]

        """Define empty lists"""
        profit_loose_lst = []
        margin_lst = []
        lot_size_lst = []
        prices_lst = []

        if is_custom_value != "Y":
            for i in fib_lst[start_point:]:
                averaging_price = Decimal(input("Add averaging price: "))
                profit_loose_lst.append(
                    round(calculate_profit_loss(pair, averaging_price, stop_price, contract_size * i), 2))
                margin_lst.append(round(calculate_margin_required(i, contract_size, averaging_price, levarage), 2))
                lot_size_lst.append(i)
                prices_lst.append(averaging_price)
                is_it_all = input("Do You want to add another Y/N?: ").upper()
                if is_it_all == 'N':
                    break
        else:
            for i in range(10):
                averaging_price = Decimal(input("Add averaging price: "))
                lot_size = Decimal(input("Add lot size: "))
                profit_loose_lst.append(
                    round(calculate_profit_loss(pair, averaging_price, stop_price, contract_size * lot_size), 2))
                margin_lst.append(round(calculate_margin_required(lot_size, contract_size, averaging_price, levarage), 2))
                lot_size_lst.append(lot_size)
                prices_lst.append(averaging_price)
                is_it_all = input("Do You want to add another Y/N?: ").upper()
                if is_it_all == 'N':
                    break

        profit_loose_lst = [-1 * x if x < 0 else x for x in profit_loose_lst]
        result_lst = profit_loose_lst + margin_lst

        if res_currency is not account_currency:
            exchange_rate = get_exchange_rate(res_currency, 'USD')
            profit_loose_lst = [round(Decimal(exchange_rate) * x, 2) for x in profit_loose_lst]
            margin_lst = [round(Decimal(exchange_rate) * x, 2) for x in margin_lst]
            result_lst = [round(Decimal(exchange_rate) * x, 2) for x in result_lst]

        data_dct = {'lot_size': lot_size_lst, 'margin_value': margin_lst, 'profit_loose_value': profit_loose_lst,
                    'price': prices_lst}
        data = pd.DataFrame(data_dct)
        data['weight'] = data['lot_size'] * 100
        data = data.assign(weighted_price=lambda x: x['price'] * x['weight'])

        weight_sum = data['weight'].sum()
        weighted_price_sum = data['weighted_price'].sum()
        weighted_average_price = weighted_price_sum / weight_sum

        pip_distance_max = round(abs(stop_price - max(data['price'])) / Decimal(minimum_price_increment))
        pip_distance_min = round(abs(stop_price - min(data['price'])) / Decimal(minimum_price_increment))

        if pip_distance_max > pip_distance_min:
            total_pips = pip_distance_max
        elif pip_distance_max < pip_distance_min:
            total_pips = pip_distance_min
        else:
            total_pips = pip_distance_max

        """ Sumup """
        print('------------------------------------------------------------------------')
        print(f'Summary {pair}: ')
        print(data)
        print('')
        print(f'Summary statistics of trade on {pair}: ')
        data = data[['lot_size', 'margin_value', 'profit_loose_value', 'price']].astype(float)
        print(data.describe().round(2))
        print('')
        print(f'The average price is: {colorama.Fore.RED}{round(weighted_average_price, 5)}{colorama.Fore.RESET}')
        print(
            f'The total margin required for this trade will be about: {colorama.Fore.RED}{round(sum(result_lst), 2)}{colorama.Fore.RESET} USD')
        print(f'which includes {colorama.Fore.RED}{round(sum(margin_lst), 2)}{colorama.Fore.RESET} USD of margin')
        print(f'and {colorama.Fore.RED}{round(sum(profit_loose_lst), 2)}{colorama.Fore.RESET} USD of profit/loose')
        print(f'The total lot size is {colorama.Fore.RED}{round(sum(lot_size_lst), 2)}{colorama.Fore.RESET}')
        print(f'The total pips distance is {colorama.Fore.RED}{round(total_pips, 2)}{colorama.Fore.RESET} pips')
        print(
            f'The ROE is: {colorama.Fore.RED}{round(sum(profit_loose_lst) / sum(margin_lst) * 100)}{colorama.Fore.RESET} %')
        print(
            f'The daily swap value for sum of lot size is: {colorama.Fore.RED}{round(swap_value_daily * sum(lot_size_lst), 2)}{colorama.Fore.RESET} USD')
        print('------------------------------------------------------------------------')

        is_email = input("Do You wan to send statistics by e mail? Y/N: ").upper()
        if is_email == "Y":
            with open("output.txt", "w") as file:
                print('------------------------------------------------------------------------', file=file)
                print(f'Summary {pair}: ', file=file)
                print(data, file=file)
                print('', file=file)
                print(f'Summary statistics of trade on {pair}: ', file=file)
                data = data[['lot_size', 'margin_value', 'profit_loose_value', 'price']]
                print(data.describe().round(2), file=file)
                print('', file=file)
                print(
                    f'The average price is: {round(weighted_average_price, 5)}',
                    file=file)
                print(
                    f'The total margin required for this trade will be about: {round(sum(result_lst), 2)} USD',
                    file=file)
                print(
                    f'which includes {round(sum(margin_lst), 2)} USD of margin',
                    file=file)
                print(
                    f'and {round(sum(profit_loose_lst), 2)} USD of profit/loose',
                    file=file)
                print(f'The total lot size is {round(sum(lot_size_lst), 2)}',
                      file=file)
                print(f'The total pips distance is {round(total_pips, 2)} pips',
                      file=file)
                print(
                    f'The ROE is: {round(sum(profit_loose_lst) / sum(margin_lst) * 100)} %',
                    file=file)
                print(
                    f'The daily swap value for sum of lot size is: {round(swap_value_daily * sum(lot_size_lst), 2)} USD',
                    file=file)
                print('------------------------------------------------------------------------', file=file)

            summary = f'Summary of {pair} trade'
            send_mail('output.txt', PASSWORD)

        option = input("Enter 'Q' to quit: ").upper()

        if option == 'Q':
            break
        else:
            continue
