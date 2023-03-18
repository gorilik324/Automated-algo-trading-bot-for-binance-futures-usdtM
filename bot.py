import json
import numpy as np
import requests
import matplotlib.pyplot as plt
import math
import hashlib
import hmac
import time

class Trader:
    def __init__(self, file):
        self.connect(file)
        self.base_url = "https://fapi.binance.com" 

    def connect(self, file):
        with open(file) as f:
            lines = f.read().splitlines()
        self.key = lines[0]
        self.secret = lines[1]

    def _generate_header(self):
        timestamp = int(time.time() * 1000)
        message = f'timestamp={timestamp}'
        signature = hmac.new(self.secret.encode(), message.encode(), hashlib.sha256).hexdigest()
        return {
            'X-MBX-APIKEY': self.key,
            'X-MBX-TIMESTAMP': str(timestamp),
            'X-MBX-SIGNATURE': signature
        }

    def get_account_balance(self):
        endpoint = '/fapi/v2/account'
        headers = self._generate_header()
        response = requests.get(f'{self.base_url}{endpoint}', headers=headers)
        data = response.json()
        return float(data['totalWalletBalance'])

    def buy(self, symbol):
        endpoint = '/fapi/v1/order'
        headers = self._generate_header()
        quantity = self.get_account_balance() / float(requests.get(f"{self.base_url}/fapi/v1/ticker/price?symbol={symbol}").json()['price'])
        params = {
            'symbol': symbol,
            'side': 'BUY',
            'type': 'MARKET',
            'quantity': balance
        }
        response = requests.post(f'{self.base_url}{endpoint}', headers=headers, params=params)
        return response.json()

    def sell(self, symbol):
        endpoint = '/fapi/v1/order'
        headers = self._generate_header()
        quantity = self.get_account_balance()
        params = {
            'symbol': symbol,
            'side': 'SELL',
            'type': 'MARKET',
            'quantity': balance
        }
        response = requests.post(f'{self.base_url}{endpoint}', headers=headers, params=params)
        return response.json()

class TechnicalAnalyzer:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def get_historical_data(self, symbol, interval):
        url = f'https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit=1000'
        headers = {'X-MBX-APIKEY': self.api_key}
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)

        close_prices = [float(entry[4]) for entry in data]
        return close_prices

    def fit_line(self, data):
        y = np.array(data)
        x = np.arange(len(y))
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        return p(x)

    def identify_dip(self, symbol, interval):
        close_prices = self.get_historical_data(symbol, interval)
        fit_line = self.fit_line(close_prices)

        lowest_line = np.min(fit_line)
        slope = np.polyfit(np.arange(len(fit_line)), fit_line, 1)[0]

        if close_prices[-1] < lowest_line and slope < 0:
            print(f'{symbol}: Dip found on {interval} timeframe')
            return True

        return False

    def identify_top(self, symbol, interval):
        close_prices = self.get_historical_data(symbol, interval)
        fit_line = self.fit_line(close_prices)

        highest_line = np.max(fit_line)
        slope = np.polyfit(np.arange(len(fit_line)), fit_line, 1)[0]

        if close_prices[-1] > highest_line and slope > 0:
            print(f'{symbol}: Top found on {interval} timeframe')
            return True

        return False


def create_sinewave(min_value, max_value, length):
    x = np.arange(length)
    y = np.sin(x * np.pi / length) * (max_value - min_value) / 2 + (max_value + min_value) / 2
    return y


filename = 'credentials.txt'
trader = Trader(filename)
analyzer = TechnicalAnalyzer(trader.key, trader.secret)

# Define amplitude
amplitude = 100

print()
trading_pairs = [symbol['symbol'] for symbol in json.loads(requests.get('https://fapi.binance.com/fapi/v1/exchangeInfo').text)['symbols']
                 if symbol['quoteAsset'] == 'USDT' and 'PERP' not in symbol['pair'].upper()]

for pair in trading_pairs:
    if analyzer.identify_dip(pair, '4h'):
        if analyzer.identify_dip(pair, '1h'):
            if analyzer.identify_dip(pair, '15m'):
                if analyzer.identify_dip(pair, '5m'):
                    print(f'{pair}: Dip confirmed on all timeframes')
                    close_prices = analyzer.get_historical_data(pair, '1m')
                    if len(close_prices) >= 200:
                        fit_line = analyzer.fit_line(close_prices[-200:])
                        current_price = close_prices[-1]
                        lowest_line = np.min(fit_line)
                        highest_line = np.max(fit_line)
                        sin_wave = np.sin(np.arange(0, 2*np.pi, 2*np.pi/200))
                        scaled_wave = (sin_wave + 1) * (highest_line - lowest_line) / 2 + lowest_line
                        if current_price <= scaled_wave[0]:
                            print(f'{pair}: Buy signal on 1m timeframe')
                            # Set the entry and exit points
                            entry_point = 0.25 * amplitude
                            exit_point = 0.75 * amplitude
                           while True:
                               # Get current market price data
                               # current_price = get_current_price(pair)
                               # Calculate sine wave value based on time
                               t = time.time()  # get current time
                               sine_wave = amplitude * math.sin(2*math.pi/period*t + shift)
                               # Check if current market price is at or below the entry point
                               if current_price <= entry_point:
                                   # Place automated buy order
                                   trader.buy(pair)
                                   #break
                               # Check if current market price is at or above the exit point
                               if current_price >= exit_point:
                                   # Close all positions and exit the market
                                   trader.close_all_positions()
                                   break
                               # Print current market price and sine wave value
                               print("Current Price:", current_price)
                               print("Sine Wave:", sine_wave)
                               # Wait for the next iteration
                               time.sleep(5)
                        elif current_price >= scaled_wave[-1]:
                            print(f'{pair}: Sell signal on 1m timeframe for mtf dip')
    elif analyzer.identify_top(pair, '4h'):
        if analyzer.identify_top(pair, '1h'):
            if analyzer.identify_top(pair, '15m'):
                if analyzer.identify_top(pair, '5m'):
                    print(f'{pair}: Top confirmed on all timeframes')
                    close_prices = analyzer.get_historical_data(pair, '1m')
                    if len(close_prices) >= 200:
                        fit_line = analyzer.fit_line(close_prices[-200:])
                        current_price = close_prices[-1]
                        lowest_line = np.min(fit_line)
                        highest_line = np.max(fit_line)
                        sin_wave = np.sin(np.arange(0, 2*np.pi, 2*np.pi/200))
                        scaled_wave = (sin_wave + 1) * (highest_line - lowest_line) / 2 + lowest_line
                        if current_price <= scaled_wave[0]:
                            print(f'{pair}: Buy signal on 1m timeframe for mtf top')
                        elif current_price >= scaled_wave[-1]:
                            print(f'{pair}: Sell signal on 1m timeframe')
                            # Set the entry and exit points
                            entry_point = 0.75 * amplitude
                            exit_point = 0.25 * amplitude
                            while True:
                                # Get current market price data
                                # current_price = get_current_price(pair)
                                # Calculate sine wave value based on time
                                t = time.time()  # get current time
                                sine_wave = amplitude * math.sin(2*math.pi/period*t + shift)
                                # Check if current market price is at or above the entry point
                                if current_price >= entry_point:
                                # Place automated sell order
                                trader.sell(pair)
                                #break
                                # Check if current market price is at or below the exit point
                                if current_price <= exit_point:
                                    # Close all positions and exit the market
                                    trader.close_all_positions()
                                    break
                                # Print current market price and sine wave value
                                print("Current Price:", current_price)
                                print("Sine Wave:", sine_wave)
                                # Wait for the next iteration
                                time.sleep(5)
print()
