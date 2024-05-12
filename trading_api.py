# 本程式基於 Sample_D.py 進行重構

import sys
import time

from PY_Trade_package.MarketDataMart import MarketDataMart, SystemEvent
from PY_Trade_package.Product import ProductBasic, ProductSnapshot, ProductTick
from PY_Trade_package.Sol_D import Sol_D
from PY_Trade_package.SolPYAPI_Model import RCode

from utils import load_yaml


class TradingAPI:

    def __init__(
        self,
        user_id,
        password,
        product_type,
        product_code,
        duration_seconds,
        detail_level=""
    ):
        self.user_id = user_id
        self.password = password
        self.product_type = product_type
        self.product_code = product_code
        self.duration_seconds = int(duration_seconds)
        self.detail_level = detail_level.upper()

        self.market_data_mart = self._setup_market_data_mart()
        self.sol_D = self._setup_sol_d()

    def run(self):
        self._login_and_subscribe()
        self._monitor_market()
        self._disconnect()

    def _setup_market_data_mart(self) -> MarketDataMart:
        market_data_mart = MarketDataMart()
        market_data_mart.OnSystemEvent = self.observer_on_system_event                 # 系統訊息通知
        market_data_mart.OnUpdateBasic = self.event_on_update_basic                    # 商品基本資料
        market_data_mart.OnMatch = self.event_on_match                                 # 成交行情
        market_data_mart.OnOrderBook = self.event_on_order_book                        # 五檔行情
        market_data_mart.OnUpdateLastSnapshot = self.observer_on_update_last_snapshot  # 國內商品最新快照更新
        return market_data_mart

    def _setup_sol_d(self):
        sol_d = Sol_D(self.market_data_mart, __file__)
        sol_d.Set_OnSystemEvent_DAPI(self.on_system_event)  # 驗證失敗訊息
        sol_d.Set_OnUpdateBasic_DAPI(self.on_update_basic)  # 驗證商品資料
        sol_d.Set_OnMatch_DAPI(self.on_match)               # 驗證成交行情
        sol_d.Set_OnLogEvent(self.event_on_log)             # 回傳錯誤通知
        sol_d.Set_OnInterruptEvent(self.event_on_interrupt)  # server回傳中斷事件
        sol_d.Set_OnAnnouncementEvent_DAPI(self.on_announcement_event)  # 公告
        sol_d.Set_OnLoginResultEvent_DAPI(self.on_login_result_event)  # 登入是否成功
        sol_d.Set_OnVerifiedEvent_DAPI(self.on_verified_event)  # 驗證成功與否
        return sol_d

    def _login_and_subscribe(self):
        is_waiting_for_verification = True
        while is_waiting_for_verification:
            result_code = self.sol_D.Login(
                self.user_id,
                self.password,
                self.product_type
            )
            if result_code == RCode.OK:
                is_waiting_for_verification = False
                print("\nConnect success.")
                self.sol_D.Subscribe(self.product_type, self.product_code)
                print(f"\nSubscribe return->{result_code}")
            else:
                if input("Enter 'Y' to retry or 'N' to exit \n").upper() == 'Y':
                    continue
                else:
                    sys.exit(0)

    def _monitor_market(self):
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > self.duration_seconds:
                break
            print(f"{int(current_time - start_time)}sec", end='', flush=True)
            time.sleep(1)

        self.sol_D.Unsubscribe(self.product_type, self.product_code)

    def _disconnect(self):
        self.sol_D.DisConnect()
        sys.exit(0)

    # Event handlers and other methods below this line
    def observer_on_system_event(self, data: SystemEvent):
        print(f"\nSystemEvent: {data}")

    def event_on_update_basic(self, data):
        if self.detail_level == "D":
            print(f"\nUpdateBasic: {data}")
        else:

            infos = {
                "Exchange": data.Exchange,
                "Symbol": data.Symbol,
                "TodayRefPrice": data.TodayRefPrice,
                "RiseStopPrice": data.RiseStopPrice,
                "FallStopPrice": data.FallStopPrice,
                "ChineseName": data.ChineseName
            }

            print(f"\nUpdateBasic: {infos}")

    def event_on_match(self, data):
        if self.detail_level == "D":
            print(f"\nOnMatch Symbol: {data}")
        else:

            infos = {
                "Symbol": data.Symbol,
                "MatchTime": data.MatchTime,
                "MatchPrice": data.MatchPrice,
                "MatchQty": data.MatchQty
            }

            print(f"\nOnMatch {infos}")

    def event_on_order_book(self, data):
        if self.detail_level == "D":
            print(f"\nOnOrder Symbol: {data}")
        else:

            infos = {
                "Symbol": data.Symbol,
                "OrderBookTime": data.OrderBookTime
            }

            print(f"\nOnOrder {infos}")

    def observer_on_update_last_snapshot(self, snapshot: ProductSnapshot):
        if self.detail_level == "D":
            print(f"\nLastSnapshot TickData: {snapshot.TickData}")
        else:

            infos = {
                "Symbol": snapshot.TickData.Symbol,
                "MatchTime": snapshot.TickData.MatchTime
            }

            print(f"\nLastSnapshot TickData: {infos}")

    def on_system_event(self, data: SystemEvent):
        "驗證失敗訊息"
        try:
            msg: str = f"[{data.rcode}]{data.msg}"
            print(msg)
        except Exception as ex:
            pass

    def on_update_basic(self, data: ProductBasic):
        "傳來驗證商品資料"
        infos = {
            "Exchange": data.Exchange,
            "Symbol": data.Symbol,
            "TodayRefPrice": data.TodayRefPrice,
            "RiseStopPrice": data.RiseStopPrice,
            "FallStopPrice": data.FallStopPrice,
            "ChineseName": data.ChineseName
        }
        print(f"\n UpdateBasic: {infos}")

    def on_match(self, data: ProductTick):
        "傳來驗證成交行情"
        try:

            infos = {
                "Symbol": data.Symbol,
                "TotalMatchQty": data.TotalMatchQty,
                "MatchPrice": data.MatchPrice,
                "MatchQty": data.MatchQty
            }

            print(f"\n OnMatch {infos}")

        except Exception as ex:
            pass

    def event_on_log(self, data):
        print(f"LogEvent: {data}")

    def event_on_interrupt(self, data):
        print(f"InterruptEvent: {data}")

    def on_announcement_event(self, data):
        "公告"
        try:
            print(f"Announcement: {data}")
        except Exception as ex:
            pass

    def on_login_result_event(self, is_succ: bool, msg: str):
        "登入是否成功"
        try:
            print(f"IsSucc:{is_succ}, Msg:{msg}")
        except Exception as ex:
            pass

    def on_verified_event(self, data):
        "驗證成功與否"
        try:
            print(f"MarketKind:{data.MarketKind}, IsSucc:{
                  data.IsSucc}, Msg:{data.Msg}")
        except Exception as ex:
            pass


if __name__ == '__main__':

    cfg = load_yaml("account.yaml")
    user_id = cfg["user"]
    password = cfg["password"]

    target = "2330"

    handler = TradingAPI(
        user_id,
        password,
        "TWS",
        target,
        duration_seconds=10,
        detail_level="D"
    )

    handler.run()
