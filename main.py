import os
import csv
import json
import random
import asyncio
from pathlib import Path

from Util.tz_util import TZUtil
from settings.settings import Settings
from quotexapi.stable_api import QuotexStableApi


# client.debug_ws_enable = True
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
# PRACTICE mode is default / REAL mode is optional
# client.set_account_mode("REAL")

class QuotexService:
  def __init__(self, settings):
    self.client = QuotexStableApi(settings)
    self.tz_util = TZUtil(settings.get('timezone'))

  async def connect(self, attempts=8):
    print("..", end="")
    for attempt in range(attempts + 1):
      if attempt == 0 or not self.client.is_connected():
        print(".", end="")
        is_connected, message = await self.client.connect()
        if is_connected:
          print()
          return True, message
        elif 'Handshake status 403 Forbidden' in message:
          continue
        else:
          print(message)
      else:
        print(message)
        sessionFile = os.path.join('.', 'session.json')
        if Path(sessionFile).exists():
          os.remove(sessionFile)
      await asyncio.sleep(5)
    return False, 'Connection Failed'


  async def create_orders(self, order_list, orders=10):
    is_connected, message = await self.connect()
    for i in range(0, orders):
      print('\n/', 80 * '=', '/', end='\n')
      print(f'OPENING ORDER: {i + 1}')
      order = random.choice(order_list)
      print(order)
      if await self.get_asset_status(order['asset']):
        status, buy_info = await self.client.buy(**order)
        await self.check_win(status, buy_info)
        print(status, buy_info)
        print('Current balance: ', await self.get_balance())
      await asyncio.sleep(2)
    print('\n/', 80 * '=', '/', end='\n')

  async def get_asset_status(self, asset):
    is_connected, message = await self.connect()
    if not is_connected: return False
    asset_query = await self.asset_parse(asset)
    asset_open = self.client.check_asset_open(asset_query)[2]
    print('✅ Asset open') if asset_open else print('❌ Asset closed.')
    return True

  async def get_balance(self):
    is_connected, message = await self.connect()
    if is_connected:
      print('Current Balance: ', await self.client.get_balance())

  async def get_candle(self, asset = 'AUDNZD_otc', offset = 180, period=60):
    await self.get_asset_status(asset)
    candles = await self.client.get_candles(asset, offset, period)
    for candle in candles['data']:
      print(f'T:{self.tz_util.utc_to_local(candle[0])}, $: {candle[1]}, ?: {candle[2]}')

  async def get_candle_v2(self, asset = 'EURUSD_otc', interval = 60): #60 to 180 sec
    if await self.get_asset_status(asset):
      candles = await self.client.get_candle_v2(asset, interval)
      for candle in candles:
        await self.write_to_csv('./data/candles.csv', candle)
      print(candles)

  async def get_open_assets(self):
    is_connected, message = await self.connect()
    open_assets = []
    if is_connected:
      for asset in self.client.get_all_asset_name():
        payment, asset, is_open = self.client.check_asset_open(asset)
        if is_open:
          open_asset = [asset, f'{payment}%']
          open_assets.append(open_asset)
          print(f'{payment}% -',asset)
    return open_assets

  async def get_payment(self, filter_open=True, sort_by_payment=True):
    is_connected, message = await self.connect()
    if is_connected:
      all_data = self.client.get_payment()
      sorted_data = sorted((data for data in all_data.items() if data[1]['open'] == filter_open),
                           key=lambda x: x[1]['payment'] if sort_by_payment else None)
      for asset_name, asset_data in sorted_data:
        print(f"{asset_data['payment']}% -", asset_name)

  async def get_profile(self):
    is_connected, message = await self.connect()
    if is_connected:
      profile = await self.client.get_profile()
      profile_description = '\n'.join(
        [f'{attr}: {getattr(profile, attr)}' for attr in dir(profile) if not attr.startswith('_') and not getattr(profile,attr) is None])
      print(profile_description)

  async def get_realtime_candle(self, asset, list_size):
    if await self.get_asset_status(asset):
      self.client.start_candles_stream(asset)
      while True:
        prices = self.client.get_realtime_candles(asset)
        if len(prices[asset]) == list_size:
          break
        for price in prices:
          await self.write_to_csv('./data/real_time_candle.csv', price)
      print(prices)

  async def get_realtime_sentiment(self, asset):
    if await self.get_asset_status(asset):
      self.client.start_candles_stream(asset)
      while True:
        sentiments = self.client.get_realtime_sentiment(asset)
        for sentiment in sentiments:
          await self.write_to_csv('./data/realtime_sentiment.csv', sentiment)
        print(sentiments, end='\r')
        await asyncio.sleep(0.5)

  async def get_signals(self):
    is_connected, message = await self.connect()
    if is_connected:
      self.client.start_signals_data()
      while True:
        signals = self.client.get_signal_data()
        for signal in signals:
          await self.write_to_csv('./data/signals.csv', signal)
        if signals:
          print(json.dumps(signals, indent=2))
        await asyncio.sleep(1)

  async def set_balance(self, new_balance=10000):
    is_connected, message = await self.connect()
    if is_connected:
      result = await self.client.edit_practice_balance(new_balance)
      print(f"New Demo Balance: {result['balance']}")

  async def asset_parse(self, asset):
    asset = asset[:3] + "/" + asset[3:]
    return asset.replace("_otc", " (OTC)") if "_otc" in asset else asset

  async def check_win(self, status, buy_info):
    print('Waiting for result...')
    if status and await self.client.check_win(buy_info['id']):
      print(f'\nWin!!! \nProfit: $ {self.client.get_profit()}')
    elif status:
      print(f'\nLoss!!! \nLoss: $ {self.client.get_profit()}')
    else:
      print('Operation failed!!!')

  async def get_instruments(self):
    print(self.client.get_all_instruments())

  async def write_to_csv(self, filename, data):
    with open(filename, 'a', newline='', encoding='utf-8') as file:
      writer = csv.writer(file)
      writer.writerow(data)


class QuotexCLI:
  def __init__(self, service):
    self.service = service

  def get_options(self):
    options = {
      'profile': self.service.get_profile,
      'balance': self.service.get_balance,
      'signals': self.service.get_signals,
      'payment': self.service.get_payment,
      'candle': self.service.get_candle,
      'candle2': self.service.get_candle_v2,
      'last_candle': self.service.get_realtime_candle,
      'sentiments': self.service.get_realtime_sentiment,
      'open_assets': self.service.get_open_assets,
      'set_balance': self.service.set_balance,
      'create_orders': self.service.create_orders,
      'instruments': self.service.get_instruments
    }
    return options

  def show_menu(self):
    print('Options (~ to end):\n' + ', '.join([f'{i + 1}. {key}' for i, key in enumerate(self.get_options().keys())]) + ': ')

  async def get_user_choice(self):
    self.show_menu()
    choice = input()
    if choice == '~': return None
    options = self.get_options()
    if choice.isdigit() and 1 <= int(choice) <= len(options):
      selected_option = list(options.keys())[int(choice) - 1]
      return selected_option
    return False

  async def handle_choice(self, choice, tasks=None):
    options = self.get_options()
    if choice == 'create_orders':
      order_list = await self.service.get_order_list()
      await options[choice](order_list)
    else:
      #if choice in ['get_candle_v2', 'get_realtime_candle', 'get_realtime_sentiment']:
        #tasks.append(options[choice]())
      #else:
      await options[choice]()

  async def set_tasks(self):
    return [
      self.service.get_candle_v2('EURUSD_otc', 60),
      self.service.get_realtime_candle('EURUSD_otc', 10),
      self.service.get_realtime_sentiment('EURUSD_otc')
    ]

  async def main_loop(self):
    #tasks = await self.set_tasks()
    while True:
      choice = await self.get_user_choice()
      if choice is None: break
      if not choice: continue
      await self.handle_choice(choice)
    #await asyncio.gather(*tasks)
    print('Exiting...')
    self.service.client.close()

if __name__ == '__main__':
  order_list = [
    {'amount': 5, 'asset': 'EURUSD_otc', 'direction': 'call', 'duration': 60},
    {'amount': 10, 'asset': 'AUDCAD_otc', 'direction': 'put', 'duration': 60},
    {'amount': 15, 'asset': 'AUDJPY_otc', 'direction': 'call', 'duration': 60},
    {'amount': 20, 'asset': 'AUDUSD_otc', 'direction': 'put', 'duration': 60},
    {'amount': 25, 'asset': 'CADJPY_otc', 'direction': 'call', 'duration': 60},
    {'amount': 30, 'asset': 'EURCHF_otc', 'direction': 'put', 'duration': 60},
    {'amount': 35, 'asset': 'EURGBP_otc', 'direction': 'call', 'duration': 60},
    {'amount': 40, 'asset': 'EURJPY_otc', 'direction': 'put', 'duration': 60},
    {'amount': 45, 'asset': 'GBPAUD_otc', 'direction': 'call', 'duration': 60},
    {'amount': 50, 'asset': 'GBPJPY_otc', 'direction': 'put', 'duration': 60},
  ]
  settings = Settings(Path('./settings/config.yml'))
  service = QuotexService(settings)
  cli = QuotexCLI(service)
  asyncio.run(cli.main_loop())
