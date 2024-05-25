import time
import math
import asyncio
import logging
from datetime import datetime
from collections import defaultdict

from . import expiration
from . import global_value
from .api import QuotexWsApi
from .constants import codes_asset

__version__ = "1.0.0"
logger = logging.getLogger(__name__)

def nested_dict(n, type):
    if n == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: nested_dict(n - 1, type))

def truncate(f, n):
    return math.floor(f * 10 ** n) / 10 ** n

class QuotexStableApi(object):
    def __init__(self, settings):
        self.size = [1, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600,
                     7200, 14400, 28800, 43200, 86400, 604800, 2592000]
        self.settings = settings
        self.set_ssid = None
        self.duration = None
        self.suspend = 0.5
        self.subscribe_candle = []
        self.subscribe_candle_all_size = []
        self.subscribe_mood = []
        self.account_is_demo = 1
        self.websocket_client = None
        self.websocket_thread = None
        self.debug_ws_enable = False
        self.api = None
        self.api_data = None

    @property
    def websocket(self):
        return self.websocket_client.wss

    @staticmethod
    def is_connected():
        return False if global_value.check_websocket_if_connect in [None, 0] else True

    async def re_subscribe_stream(self):
        subscriptions = [
            (self.subscribe_candle, self.start_candles_one_stream, True),
            (self.subscribe_candle_all_size, self.start_candles_all_size_stream, False),
            (self.subscribe_mood, self.start_mood_stream, False)
        ]
        for subscription_list, start_method, split_needed in subscriptions:
            try:
                for subscription in subscription_list:
                    if split_needed:
                        asset, candle_size = subscription.split(",")
                        await start_method(asset, candle_size)
                    else:
                        await start_method(subscription)
            except:
                pass

    async def get_instruments(self):
        await asyncio.sleep(self.suspend)
        self.api.instruments = None
        while self.api.instruments is None:
            try:
                await self.api.get_instruments()
                start = time.time()
                while self.api.instruments is None and time.time() - start < 10:
                    await asyncio.sleep(0.1)
            except:
                logger.error('**error** api.get_instruments need reconnect')
                await self.connect()
        return self.api.instruments

    def get_all_instruments(self):
        if self.api.instruments:
            return self.api.instruments

    def get_all_asset_name(self):
        if self.api.instruments:
            return [instrument[2].replace("\n", "") for instrument in self.api.instruments]

    def check_asset_open(self, instrument):
        if self.api.instruments:
            for i in self.api.instruments:
                if instrument == i[2]:
                    self.api.current_asset = instrument.replace("/", "")
                    return i[0], i[2], i[14]

    async def get_candles(self, asset, offset, period=None):
        index = expiration.get_timestamp()
        # index - offset
        if period:
            period = expiration.get_period_time(period)
        else:
            period = index
        self.api.current_asset = asset
        self.api.candles._list = None
        self.start_candles_stream(asset)
        while True:
            try:
                self.api.get_candles(codes_asset[asset], offset, period, index)
                while self.is_connected and self.api.candles._list is None:
                    await asyncio.sleep(0.1)
                if self.api.candles._list is not None:
                    break
            except:
                logger.error('**error** get_candles need reconnect')
                await self.connect()
        return self.api.candles._list

    async def get_candle_v2(self, asset, period):
        self.api.candle_v2_data[asset] = None
        self.stop_candles_stream(asset)
        self.api.subscribe_realtime_candle(asset, period)
        while self.api.candle_v2_data[asset] is None:
            await asyncio.sleep(0.1)
        return self.api.candle_v2_data[asset]

    async def connect(self):
        if self.is_connected(): return True, 'OK'
        self.api = QuotexWsApi(self.settings)
        self.api.trace_ws = self.debug_ws_enable
        is_connected, message = await self.api.connect(self.account_is_demo)
        if is_connected:
            self.api_data = self.api.send_ssid()
            if global_value.check_accepted_connection == 0:
                is_connected, message = await self.connect()
                if not is_connected:
                    is_connected, message = is_connected, "Session unset"
        return is_connected, message

    def set_account_mode(self, balance_mode="PRACTICE"):
        acc_mode = {"REAL": 0, "PRACTICE": 1}
        try:
            self.account_is_demo = acc_mode[balance_mode.upper()]
        except KeyError:
            logger.error("ERROR doesn't have this mode")
            exit(1)

    def change_account(self, balance_mode):
        self.account_is_demo = 0 if balance_mode.upper() == "REAL" else 1

    async def edit_practice_balance(self, amount=None):
        self.api.training_balance_edit_request = None
        self.api.edit_training_balance(amount)
        while self.api.training_balance_edit_request is None:
            await asyncio.sleep(0.1)
        return self.api.training_balance_edit_request

    async def get_balance(self):
        while self.api.account_balance is None:
            await asyncio.sleep(0.1)
        balance = self.api.account_balance.get("demoBalance") \
            if self.api.account_type > 0 else self.api.account_balance.get("liveBalance")
        return float(f"{truncate(balance + self.get_profit(), 2):.2f}")

    async def get_profile(self):
        return await self.api.get_profile()

    async def buy(self, amount, asset, direction, duration):
        request_id = expiration.get_timestamp()
        self.api.current_asset = asset
        self.api.subscribe_realtime_candle(asset, duration)
        self.api.buy(amount, asset, direction, duration, request_id)

        try:
            await asyncio.wait_for(self._api_buy_id(), timeout=duration)
            status_buy = True if self.api.buy_id is not None else False
        except asyncio.TimeoutError:
            status_buy = False
        if global_value.check_websocket_if_error:
            return False, global_value.websocket_error_reason
        return status_buy, self.api.buy_successful

    async def _api_buy_id(self):
        while self.api.buy_id is None:
            await asyncio.sleep(0.1)

    async def sell_option(self, options_ids):
        self.api.sell_option(options_ids)
        self.api.sold_options_respond = None
        try:
            await asyncio.wait_for(self._api_sold_options(), timeout=10)
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for sold options response")
        return self.api.sold_options_respond

    async def _api_sold_options(self):
        while self.api.sold_options_respond is None:
            await asyncio.sleep(0.1)

    def get_payment(self):
        return {i[2]: {"turbo_payment": i[18], "payment": i[5], "open": i[14]} for i in self.api.instruments}

    async def start_remaining_time(self):
        now_stamp = datetime.fromtimestamp(expiration.get_timestamp())
        expiration_stamp = datetime.fromtimestamp(self.api.timesync.server_timestamp)
        remaining_time = int((expiration_stamp - now_stamp).total_seconds())
        try:
            for i in range(remaining_time, -1, -1):
                print(f"\rMissing {i if i > 0 else 0} seconds ...", end="")
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            print("\nCountdown was cancelled.")

    async def check_win(self, id_number):
        await self.start_remaing_time()
        while True:
            try:
                listinfodata_dict = self.api.listinfodata.get(id_number)
                if listinfodata_dict["game_state"] == 1: break
            except: pass
        self.api.listinfodata.delete(id_number)
        return listinfodata_dict["win"]

    def start_candles_stream(self, asset, period=0):
        self.api.follow_candle(asset)
        self.api.subscribe_realtime_candle(asset, period)

    def stop_candles_stream(self, asset):
        self.api.unfollow_candle(asset)
        self.api.unsubscribe_realtime_candle(asset)

    def start_signals_data(self):
        self.api.signals_subscribe()

    def get_realtime_candles(self, asset):
        while True:
            if self.api.realtime_price.get(asset):
                return self.api.realtime_price
            time.sleep(0.1)

    def get_realtime_sentiment(self, asset):
        while True:
            if self.api.realtime_sentiment.get(asset):
                return self.api.realtime_sentiment
            time.sleep(0.1)

    def get_signal_data(self):
        return self.api.signal_data

    def get_profit(self):
        return self.api.profit_in_operation or 0

    async def start_candles_one_stream(self, asset, size):
        if not (str(asset + "," + str(size)) in self.subscribe_candle):
            self.subscribe_candle.append((asset + "," + str(size)))
        start = time.time()
        self.api.candle_generated_check[str(asset)][int(size)] = {}
        while True:
            if time.time() - start > 20:
                logger.error('**error** start_candles_one_stream late for 20 sec')
                return False
            try:
                if self.api.candle_generated_check[str(asset)][int(size)]:
                    return True
            except:
                pass
            try:
                self.api.follow_candle(codes_asset[asset])
            except:
                logger.error('**error** start_candles_stream reconnect')
                await self.connect()
            await asyncio.sleep(0.1)

    async def start_candles_all_size_stream(self, asset):
        self.api.candle_generated_all_size_check[str(asset)] = {}
        if not (str(asset) in self.subscribe_candle_all_size):
            self.subscribe_candle_all_size.append(str(asset))
        start = time.time()
        while True:
            if time.time() - start > 20:
                logger.error(f'**error** fail {asset} start_candles_all_size_stream late for 10 sec')
                return False
            try:
                if self.api.candle_generated_all_size_check[str(asset)]:
                    return True
            except:
                pass
            try:
                self.api.subscribe_all_size(codes_asset[asset])
            except:
                logger.error(
                    '**error** start_candles_all_size_stream reconnect')
                await self.connect()
            await asyncio.sleep(0.1)

    async def start_mood_stream(self, asset, instrument="turbo-option"):
        if asset not in self.subscribe_mood:
            self.subscribe_mood.append(asset)
        while True:
            self.api.subscribe_Traders_mood(
                asset[asset], instrument)
            try:
                self.api.traders_mood[codes_asset[asset]] = codes_asset[asset]
                break
            except:
                await asyncio.sleep(0.1)

    def close(self):
        return self.api.close()
