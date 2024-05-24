import os
import time
import json
import ssl
import logging
import platform
import threading
from pathlib import Path
from collections import defaultdict
from websocket import WebSocketConnectionClosedException
import urllib3
import certifi

from .http.qx_login import Login
from .http.qx_logout import Logout
from .http.qx_browser_settings import QxBrowserSettings
from .ws.channels.ssid import Ssid
from .ws.channels.buy import Buy
from .ws.channels.candles import GetCandles
from .ws.channels.sell_option import SellOption
from .ws.objects.timesync import TimeSync
from .ws.objects.candles import Candles
from .ws.objects.profile import Profile
from .ws.objects.listinfodata import ListInfoData
from .ws.client import WebsocketClient
from . import global_value

urllib3.disable_warnings()
logger = logging.getLogger(__name__)

os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['WEBSOCKET_CLIENT_CA_BUNDLE'] = certifi.where()


class QuotexWssApi:
    def __init__(self, settings):
        self.settings = settings
        self.proxies = settings.get("proxies")
        self.wss_host = settings.get("host")
        self.session_data = {}
        self.realtime_price = {}
        self.profile = Profile()
        self.candles = Candles()
        self.timesync = TimeSync()
        self.listinfodata = ListInfoData()
        self.websocket_client = None
        self.websocket_thread = None
        self.wss_message = None
        self.profit_in_operation = None

    @property
    def websocket(self):
        return self.websocket_client.wss

    def send_request(self, data):
        while global_value.ssl_Mutual_exclusion or global_value.ssl_Mutual_exclusion_write:
            pass
        global_value.ssl_Mutual_exclusion_write = True
        try:
            self.websocket.send(data)
        except WebSocketConnectionClosedException:
            self.connect()
            self.websocket.send(data)
        logger.debug(data)
        global_value.ssl_Mutual_exclusion_write = False

    def subscribe_realtime_candle(self, asset, period):
        self.realtime_price[asset] = []
        data = f'42["instruments/update", {json.dumps({"asset": asset, "period": period})}]'
        self.send_request(data)

    def follow_candle(self, asset):
        data = f'42["depth/follow", {json.dumps(asset)}]'
        self.send_request(data)

    def unfollow_candle(self, asset):
        data = f'42["depth/unfollow", {json.dumps(asset)}]'
        self.send_request(data)

    def unsubscribe_realtime_candle(self, asset):
        data = f'42["subfor", {json.dumps(asset)}]'
        self.send_request(data)

    def edit_training_balance(self, amount):
        data = f'42["demo/refill", {json.dumps(amount)}]'
        self.send_request(data)

    def signals_subscribe(self):
        self.send_request('42["signal/subscribe"]')

    async def get_profile(self):
        profile_data = QxBrowserSettings(self).get().get("data")
        self.profile.nick_name = profile_data["nickname"]
        self.profile.profile_id = profile_data["id"]
        self.profile.demo_balance = profile_data["demoBalance"]
        self.profile.live_balance = profile_data["liveBalance"]
        self.profile.avatar = profile_data["avatar"]
        self.profile.currency_code = profile_data["currencyCode"]
        self.profile.country = profile_data["country"]
        self.profile.country_name = profile_data["countryName"]
        self.profile.currency_symbol = profile_data["currencySymbol"]
        return self.profile

    async def check_session(self):
        session_file = os.path.join(self.settings.get("resource_path"), "session.json")
        if os.path.isfile(session_file):
            try:
                with open(session_file) as file:
                    self.session_data = json.loads(file.read())
            except Exception as e:
                logger.error(e)

    async def autenticate(self):
        await self.check_session()
        if not self.session_data.get("token"):
            print("Logging in ... ", end="")
            await self.login(self.settings)
            if self.session_data.get("token"):
                print("✅ OK")

    async def start_websocket(self, reconnect):
        if not reconnect:
            await self.autenticate()
        global_value.check_websocket_if_connect = None
        global_value.check_websocket_if_error = False
        global_value.websocket_error_reason = None
        self.websocket_client = WebsocketClient(self)
        payload = {
            "ping_interval": 25,
            "ping_timeout": 15,
            "ping_payload": "2",
            "origin": "https://qxbroker.com",
            "host": "ws2.qxbroker.com",
            "sslopt": {"cert_reqs": ssl.CERT_NONE, "ca_certs": certifi.where()}
        }
        if platform.system() == "Linux":
            payload["sslopt"]["ssl_version"] = ssl.PROTOCOL_TLSv1_2
        self.websocket_thread = threading.Thread(target=self.websocket.run_forever, kwargs=payload)
        self.websocket_thread.daemon = True
        self.websocket_thread.start()
        while True:
            if global_value.check_websocket_if_error:
                return False, global_value.websocket_error_reason
            if global_value.check_websocket_if_connect == 0:
                logger.debug("Websocket connection closed.")
                return False, "Websocket connection closed."
            if global_value.check_websocket_if_connect == 1:
                logger.debug("Websocket successfully connected.")
                return True, "Websocket successfully connected."

    def send_ssid(self):
        self.wss_message = None
        if not global_value.SSID:
            session_file = os.path.join(self.settings.get("resource_path"), "session.json")
            if os.path.exists(session_file):
                os.remove(session_file)
            return False
        self.ssid(global_value.SSID)
        while not self.wss_message:
            time.sleep(0.3)
        return bool(self.wss_message)

    async def connect(self, is_demo=1, reconnect=False):
        self.account_type = is_demo
        global_value.ssl_Mutual_exclusion = False
        global_value.ssl_Mutual_exclusion_write = False
        if global_value.check_websocket_if_connect:
            logger.info("Closing websocket connection...")
            self.close()
        check_websocket, websocket_reason = await self.start_websocket(reconnect)
        if check_websocket and not global_value.SSID:
            global_value.SSID = self.session_data.get("token")
        return check_websocket, websocket_reason

    async def reconnect(self):
        logger.info("Websocket Reconnection...")
        await self.start_websocket(reconnect=True)

    def close(self):
        if self.websocket_client:
            self.websocket.close()
            self.websocket_thread.join()
        return True

    def websocket_alive(self):
        return self.websocket_thread.is_alive()

    @property
    def logout(self):
        return Logout(self)

    @property
    def login(self):
        return Login(self)

    @property
    def ssid(self):
        return Ssid(self)

    @property
    def buy(self):
        return Buy(self)

    @property
    def sell_option(self):
        return SellOption(self)

    @property
    def get_candles(self):
        return GetCandles(self)
