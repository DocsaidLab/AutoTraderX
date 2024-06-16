import signal
import sys
import time
from typing import List

from PY_Trade_package.MarketDataMart import MarketDataMart, SystemEvent
from PY_Trade_package.Product import ProductBasic, ProductTick
from PY_Trade_package.Sol_D import Sol_D
from PY_Trade_package.SolPYAPI_Model import RCode

from .utils import load_yaml, now


class QuotationSystem:

    def __init__(
        self,
        user: str,
        password: str,
        product_type: str = "TWS",
        subscribe_list: List[str] = [],
    ):
        self.user = user
        self.password = password
        self.product_type = product_type
        self.subscribe_list = subscribe_list
        self.stock_infos = {}

        market_data_mart: MarketDataMart = self._setup_market_data_mart()
        self.sol_D: Sol_D = self._setup_sol_d(market_data_mart) # 相依性注入

        self.login()
        for prod_code in subscribe_list:
            self.sol_D.Subscribe(product_type, prod_code)

            # 建立初始成交紀錄表
            markdown_lines = []
            markdown_lines.append(f"# 日成交資料 - {prod_code}\n")
            markdown_lines.append("| 成交時間 | 成交價 | 漲跌 | 成交量 | 總量 |")
            markdown_lines.append("| ---- | ---- | ---- | ---- | ---- |")
            formatted_text = "\n".join(markdown_lines)

            with open(f'log_{now("%Y%m%d")}_{prod_code}_match.md', "a", encoding="utf-8") as f:
                f.write(formatted_text)

        signal.signal(signal.SIGINT, self.signal_handler)
        while True:
            sys.stdout.write("\rPress 'Ctrl + C' to exit the program.")
            sys.stdout.flush()
            time.sleep(1)

    def login(self):

        # 透過元富 API 登入
        result_code = self.sol_D.Login(
            self.user,
            self.password,
            self.product_type
        )

        if result_code == RCode.OK:
            print("\nConnect success.")
        else:
            print("\nConnect failed.")
            self.disconnect()

    def signal_handler(self, signal, frame):
        print('\n\nYou pressed Ctrl+C, Stopping the program...\n')
        self.disconnect()

    def disconnect(self):
        if len(self.subscribe_list):
            for prod_code in self.subscribe_list:
                self.sol_D.Unsubscribe(self.product_type, prod_code)
        self.sol_D.DisConnect()
        sys.exit(0)

    def _setup_market_data_mart(self) -> MarketDataMart:
        market_data_mart = MarketDataMart()
        market_data_mart.OnSystemEvent = self.observer_on_system_event  # 系統訊息通知
        market_data_mart.OnUpdateBasic = self.event_on_update_basic     # 商品基本資料
        market_data_mart.OnMatch = self.event_on_match                  # 成交行情
        market_data_mart.OnOrderBook = self.event_on_order_book         # 五檔行情
        return market_data_mart

    def _setup_sol_d(self, market_data_mart: MarketDataMart) -> Sol_D:
        sol_d = Sol_D(market_data_mart, __file__)
        sol_d.Set_OnSystemEvent_DAPI(self.on_system_event)  # 驗證失敗訊息
        sol_d.Set_OnUpdateBasic_DAPI(self.on_update_basic)  # 驗證商品資料
        sol_d.Set_OnMatch_DAPI(self.on_match)               # 驗證成交行情
        sol_d.Set_OnLogEvent(self.event_on_log)             # 回傳錯誤通知
        sol_d.Set_OnInterruptEvent(self.event_on_interrupt)  # server回傳中斷事件
        sol_d.Set_OnAnnouncementEvent_DAPI(self.on_announcement_event)  # 公告
        sol_d.Set_OnLoginResultEvent_DAPI(self.on_login_result_event)  # 登入是否成功
        sol_d.Set_OnVerifiedEvent_DAPI(self.on_verified_event)  # 驗證成功與否
        return sol_d

    def observer_on_system_event(self, data: SystemEvent):
        print(f"\系統訊息: {data}")

    def event_on_update_basic(self, data):
        """ 紀錄商品基本資料 """

        infos = {
            "中文名稱": data.ChineseName,
            "交易所代碼": data.Exchange,
            "參考價": data.TodayRefPrice,
            "漲停價": data.RiseStopPrice,
            "跌停價": data.FallStopPrice,
            "上一交易日成交總量": data.PreTotalMatchQty,
            "上一交易日參考價": data.PreTodayRefPrice,
            "上一交易日收盤價": data.PreClosePrice,
            "產業別": data.IndustryCategory,
            "股票異常代碼": data.StockAnomalyCode,
            "非十元面額註記": data.NonTenParValueRemark,
            "異常推介個股註記": data.AbnormalRecommendationIndicator,
            "可現股當沖註記": data.DayTradingRemark,
            "交易單位": data.TradingUnit,
        }

        # Update main attribute
        self.stock_infos[data.Symbol] = {
            "chinese_name": data.ChineseName,
            "exchange": data.Exchange,
            "today_ref_price": data.TodayRefPrice,
            "rise_stop_price": data.RiseStopPrice,
            "fall_stop_price": data.FallStopPrice,
            "pre_total_match_qty": data.PreTotalMatchQty,
            "pre_today_ref_price": data.PreTodayRefPrice,
            "pre_close_price": data.PreClosePrice,
        }

        # Markdown 表格輸出
        markdown_lines = []
        markdown_lines.append(f"# 交易紀錄 - {data.Symbol}\n")
        markdown_lines.append(f"## 商品基本資料\n")
        markdown_lines.append("| 項目 | 數值 |")
        markdown_lines.append("| ---- | ---- |")

        for key, value in infos.items():
            markdown_lines.append(f"| {key} | {value} |")

        formatted_text = "\n".join(markdown_lines)

        with open(f'log_{now("%Y%m%d")}_{data.Symbol}_info.md', "a", encoding="utf-8") as f:
            f.write(formatted_text)

    def event_on_order_book(self, data):
        """ 接收五檔行情資料 """
        self.buy_prices = data.BuyPrice
        self.buy_qtys = data.BuyQty
        self.sell_prices = data.SellPrice
        self.sell_qtys = data.SellQty

    def event_on_match(self, data):
        """ 接收成交行情資料 """

        pre_close_price = self.stock_infos[data.Symbol]["pre_close_price"]
        diff = float(data.MatchPrice) - float(pre_close_price)
        diff = diff
        if diff >= 0:
            diff = f"+{diff:.3f}"
        else:
            diff = f"{diff:.3f}"

        formatted_text = f"| {data.MatchTime} | {data.MatchPrice} | {diff} | {data.MatchQty} | {data.TotalMatchQty}\n"
        with open(f'log_{now("%Y%m%d")}_{data.Symbol}_match.md', "a", encoding="utf-8") as f:
            f.write(formatted_text)

    def on_system_event(self, data: SystemEvent):
        """ 驗證失敗訊息 """
        try:
            msg: str = f"[{data.rcode}]{data.msg}"
            print(msg)
        except Exception as ex:
            pass

    def on_update_basic(self, data: ProductBasic):
        """ 傳來驗證商品資料 """
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
        """ 傳來驗證成交行情 """
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
        """ 公告 """
        try:
            print(f"Announcement: {data}")
        except Exception as ex:
            pass

    def on_login_result_event(self, is_succ: bool, msg: str):
        """ 登入是否成功 """
        try:
            print(f"IsSucc:{is_succ}, Msg:{msg}")
        except Exception as ex:
            pass

    def on_verified_event(self, data):
        """ 驗證成功與否 """
        try:
            print(f"MarketKind:{data.MarketKind}, IsSucc:{data.IsSucc}, Msg:{data.Msg}")
        except Exception as ex:
            pass


if __name__ == '__main__':

    cfg = load_yaml("account.yaml")
    user = cfg["user"]
    password = cfg["password"]


    handler = QuotationSystem(
        user=user,
        password=password,
        subscribe_list=["2409", "2884"]
    )
