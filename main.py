import os
import sys
from pathlib import Path
from typing import Dict, List, Union
from warnings import warn

from MasterTradePy.api import MasterTradeAPI
from MasterTradePy.constant import (OrderType, PriceType, RCode, Side,
                                    TradingSession, TradingUnit)
from MasterTradePy.model import *

from quotation_system import QuotationSystem
from utils import ConcreteMarketTrader, get_curdir, get_files, load_yaml

DIR = get_curdir(__file__)


class AutoTraderX:

    def __init__(
        self,
        is_sim: bool = True,    # 是否連測試主機
        is_force: bool = True,  # 是否單一帳號通過強制登入
        is_event: bool = False,  # 是否連接競賽主機
        target: str = None,     # 操作標的
    ):
        cfg = load_yaml(DIR / "account.yaml")

        self.username = cfg["user"]
        self.password = cfg["password"]
        self.account_number = cfg["account_number"]
        self.is_sim = is_sim
        self.is_force = is_force
        self.is_event = is_event
        self.status = None

        # self.quotation = QuotationSystem(self.username, self.password, target)

    def login(self):
        trader = ConcreteMarketTrader()
        self.api = MasterTradeAPI(trader)
        self.api.SetConnectionHost('solace140.masterlink.com.tw:55555')

        # 登入
        rc = self.api.Login(self.username, self.password,
                            self.is_sim, self.is_force, self.is_event)
        if rc != RCode.OK:
            print("登入失敗，請檢查使用者名稱和密碼是否正確")

        self.status = True

    def stop(self):
        self.api.disClient()
        self.status = False

    # 查詢委託回報
    def get_order_report(self) -> List[Dict[str, Union[str, int]]]:
        self.api.QryRepAll(self.account_number)

    # 查詢庫存
    def get_inventory(self) -> List[Dict[str, Union[str, int]]]:
        # 這個 qid 似乎不是一個即時的回傳結果，必須有 pause 才能看到輸出
        # 這裡之後看要怎麼串接這個回傳結果
        qid = self.api.ReqInventoryRayinTotal(self.account_number)
        print(f"\n\n查詢庫存...{qid}\n\n")

    # 查詢成交回報
    def get_trade_report(self) -> List[Dict[str, Union[str, int]]]:
        self.api.QryRepDeal(self.account_number)

    # 查詢委託回報
    def get_order_report(self) -> List[Dict[str, Union[str, int]]]:
        self.api.QryRepAll(self.account_number)

    def set_order(
        self,
        symbol: str,    # 股票代號
        side: Side,     # 買賣別
        qty: int,       # 委託股數
        price: float,   # 委託價格
        order_type: OrderType = OrderType.ROD,  # 委託類型
        price_type: PriceType = PriceType.MKT,  # 價格類型
        trading_session: TradingSession = TradingSession.NORMAL,  # 交易時段
        trading_unit: TradingUnit = TradingUnit.COMMON,  # 交易單位
    ):
        self.api.ReqBasic(symbol)

        order = Order(
            tradingSession=trading_session,
            side=side,
            symbol=symbol,
            priceType=price_type,
            price=price,
            tradingUnit=trading_unit,
            qty=qty,
            orderType=order_type,
            tradingAccount=self.account_number,
            userDef=''
        )
        rc = self.api.NewOrder(order)
        if rc == RCode.OK:
            print(u'已送出委託')
        else:
            print(u'下單失敗! 請再次執行程式，依據回報資料修正輸入')

    def buy(self, symbol: str, qty: int, price: float):
        self.set_order(symbol, Side.BUY, qty * 1000, price)

    def sell(self, symbol: str, qty: int, price: float):
        self.set_order(symbol, Side.SELL, qty * 1000, price)

    def strategy(self):
        # 交易策略寫在這裡
        pass


handler = AutoTraderX(is_sim=False)

handler.login()
handler.get_inventory()
# os.system("pause")
# handler.get_order_report()
# handler.get_trade_report()
handler.stop()
