import signal
import sys
import time
from copy import deepcopy
from typing import Callable

from prettytable import PrettyTable
from PY_Trade_package.MarketDataMart import MarketDataMart, SystemEvent
from PY_Trade_package.Product import ProductBasic, ProductTick
from PY_Trade_package.Sol_D import Sol_D
from PY_Trade_package.SolPYAPI_Model import RCode

from .utils import COLORSTR, colorstr, load_yaml, now


class Stock:

    def __init__(
        self,
        user,
        password,
        product_code,
        product_type: str = "TWS",
        verbose: bool = False,
        day_trading_strategy: Callable = None
    ):
        self.user = user
        self.password = password
        self.product_code = product_code
        self.product_type = product_type
        self.verbose = verbose
        self.day_trading_strategy = day_trading_strategy

        # Log match infos
        self._log_match("成交時間", "成交價", "成交量", "累積成交量")
        if self.verbose:
            self.match_table = PrettyTable()
            self.match_table.field_names = ["成交時間", "成交價", "成交量", "累計成交量"]
            self.match_table.align = "c"
            self.match_table.align["成交時間"] = "r"
            self.match_table.align["成交價"] = "r"
            self.match_table.align["成交量"] = "r"
            self.match_table.align["累計成交量"] = "r"

        market_data_mart: MarketDataMart = self._setup_market_data_mart()
        self.sol_D: Sol_D = self._setup_sol_d(market_data_mart) # 相依性注入

        signal.signal(signal.SIGINT, self.signal_handler)
        self._login_and_subscribe()

    def _login_and_subscribe(self):

        # 使用元富 API 登入
        result_code = self.sol_D.Login(
            self.user,
            self.password,
            self.product_type
        )

        if result_code == RCode.OK:
            print("\nConnect success.")
            self.sol_D.Subscribe(self.product_type, self.product_code)
        else:
            print("\nConnect failed.")
            self.sol_D.Unsubscribe(self.product_type, self.product_code)
            self.sol_D.DisConnect()
            sys.exit(0)

        while True:
            # 接收其他鍵盤事件
            sys.stdout.write("\rPress 'Ctrl + C' to exit the program.")
            sys.stdout.flush()
            time.sleep(1)

    def _disconnect(self):
        self.sol_D.Unsubscribe(self.product_type, self.product_code)
        self.sol_D.DisConnect()
        sys.exit(0)

    def signal_handler(self, signal, frame):
        print('\n\nYou pressed Ctrl+C, Stopping the program...\n')
        self._disconnect()

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

    # Event handlers and other methods below this line
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
        self.symbol = data.Symbol
        self.chinese_name = data.ChineseName
        self.exchange = data.Exchange
        self.today_ref_price = data.TodayRefPrice
        self.rise_stop_price = data.RiseStopPrice
        self.fall_stop_price = data.FallStopPrice
        self.pre_total_match_qty = data.PreTotalMatchQty
        self.pre_today_ref_price = data.PreTodayRefPrice
        self.pre_close_price = data.PreClosePrice

        # 格式化為表格輸出
        table = PrettyTable()
        table.field_names = [f"商品：{data.Symbol}", "數值"]
        for key, value in infos.items():
            table.add_row([key, value])

        table.align = "l"
        table.align["數值"] = "r"  # 右對齊

        print('\n')
        print(table)
        print('\n')

    def show_order_book(self):

        # Lock
        buy_prices = deepcopy(self.buy_prices)
        buy_qtys = deepcopy(self.buy_qtys)
        sell_prices = deepcopy(self.sell_prices)
        sell_qtys = deepcopy(self.sell_qtys)

        # table = PrettyTable()
        # table.field_names = ["買入量", "買入價", "賣出價", "賣出量"]

        # for i in range(5):

        #     if float(buy_prices[i]) < float(self.pre_close_price):
        #         _buy_prices = colorstr(buy_prices[i], COLORSTR.GREEN)
        #     elif float(buy_prices) > float(self.pre_close_price):
        #         _buy_prices = colorstr(buy_prices[i], COLORSTR.RED)
        #     else:
        #         _buy_prices = colorstr(buy_prices[i], COLORSTR.YELLOW)

        #     if float(sell_prices[i]) < float(self.pre_close_price):
        #         _sell_prices = colorstr(sell_prices[i], COLORSTR.GREEN)
        #     elif float(sell_prices[i]) > float(self.pre_close_price):
        #         _sell_prices = colorstr(sell_prices[i], COLORSTR.RED)
        #     else:
        #         _sell_prices = colorstr(sell_prices[i], COLORSTR.YELLOW)

        #     _buy_qtys = colorstr(buy_qtys[i], COLORSTR.YELLOW)
        #     _sell_qtys = colorstr(sell_qtys[i], COLORSTR.YELLOW)

        #     table.add_row([
        #         _buy_qtys,
        #         _buy_prices,
        #         _sell_prices,
        #         _sell_qtys
        #     ])

        # table.align = "c"
        # table.align["買入價"] = "r"
        # table.align["買入量"] = "r"
        # table.align["賣出價"] = "r"
        # table.align["賣出量"] = "r"

        # curr_time = datetime.now()
        # curr_time = curr_time.strftime("%Y-%m-%d %H:%M:%S.%f")

        # if self.verbose:
        #     print(f"\n即時五檔資料:\n{curr_time}")
        #     print(table)

    def _log_match(self, time, price, volumn, total):
        with open(f'{now("%Y%m%d")}_match_log_{self.product_code}.txt', "a", encoding="utf-8") as f:
            f.write(f"{time}, {price}, {volumn}, {total}\n")

    def log_match(self):

        # Lock
        match_time = deepcopy(self.match_time)
        match_price = deepcopy(self.match_price)
        match_qty = deepcopy(self.match_qty)
        total_match_qty = deepcopy(self.total_match_qty)

        # Write to file
        self._log_match(match_time, match_price, match_qty, total_match_qty)

        if self.verbose:
            if float(match_price) < float(self.pre_close_price):
                _match_price = colorstr(match_price, COLORSTR.GREEN)
            elif float(match_price) > float(self.pre_close_price):
                _match_price = colorstr(match_price, COLORSTR.RED)
            else:
                _match_price = colorstr(match_price, COLORSTR.YELLOW)

            if str(match_price) in self.buy_prices:
                _match_qty = colorstr(match_qty, COLORSTR.RED)
            elif str(match_price) in self.sell_prices:
                _match_qty = colorstr(match_qty, COLORSTR.GREEN)
            else:
                _match_qty = colorstr(match_qty, COLORSTR.YELLOW)

            _total_match_qty = colorstr(total_match_qty, COLORSTR.YELLOW)

            # Append
            self.match_table.add_row([
                match_time,
                _match_price,
                _match_qty,
                _total_match_qty
            ])

            print("\n即時成交資料:")
            print(self.match_table)

    def event_on_order_book(self, data):
        """ 接收五檔行情資料 """
        self.buy_prices = data.BuyPrice
        self.buy_qtys = data.BuyQty
        self.sell_prices = data.SellPrice
        self.sell_qtys = data.SellQty
        self.show_order_book()

    def event_on_match(self, data):
        """ 接收成交行情資料 """
        self.match_time = data.MatchTime
        self.match_price = data.MatchPrice
        self.match_qty = data.MatchQty
        self.total_match_qty = data.TotalMatchQty
        self.log_match()

        # 套用當沖策略
        if isinstance(self.day_trading_strategy, Callable):
            self.day_trading_strategy(
                time=self.match_time,
                price=self.match_price,
                qty=self.match_qty,
                total_qty=self.total_match_qty
            )

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

    target = "2884"

    handler = Stock(
        user,
        password,
        target
    )
