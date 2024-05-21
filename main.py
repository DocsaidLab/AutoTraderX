import os
import sys
import time
from pathlib import Path
from pprint import pprint
from typing import Dict, List, Union
from warnings import warn

from MasterTradePy.api import MasterTradeAPI
from MasterTradePy.constant import (OrderType, PriceType, RCode, Side,
                                    TradingSession, TradingUnit)
from MasterTradePy.model import *
from prettytable import PrettyTable

from quotation_system import QuotationSystem
from utils import (ConcreteMarketTrader, get_curdir, get_files, load_yaml,
                   translate)

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
        self.trader = ConcreteMarketTrader()
        self.api = MasterTradeAPI(self.trader)
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

        print(f"\n\n查詢委託...\n\n")

        data = translate(self.trader.reports)

        # Create a PrettyTable object
        table = PrettyTable()

        # Customizing the table headers based on data needs
        table.field_names = [
            "類型", "委託書號", "股票代號", "狀態", "訊息", "委託價", "委託量", "成交量"
        ]

        # Add rows to the table after processing detail data
        for entry in data:
            details = entry.pop('詳細資料')
            price = details.get('price', '')
            orgQty = details.get('orgQty', '')
            cumQty = details.get('cumQty', '')

            # Clean status and message fields
            status = entry['狀態'].split(')')[-1]
            message = entry['訊息'].replace('Tws:48:', '').strip()

            # Translate table names
            table_name_translation = {
                "RPT:TwsNew": "新報告",
                "ORD:TwsOrd": "委託訂單",
                "RPT:TwsDeal": "交易報告"
            }
            translated_table_name = table_name_translation.get(
                entry["表格名稱"], entry["表格名稱"])

            # Append processed data into the table
            row = [
                translated_table_name,
                entry["委託書號"],
                entry["股票代號"],
                status,
                message,
                price,
                orgQty,
                cumQty
            ]
            table.add_row(row)

        # Set column alignments
        table.align = "c"
        table.align["委託價"] = "r"
        table.align["委託量"] = "r"
        table.align["成交量"] = "r"

        # Print the table
        print(table)

    # 查詢庫存
    def get_inventory(self) -> List[Dict[str, Union[str, int]]]:
        qid = self.api.ReqInventoryRayinTotal(self.account_number)
        print(f"\n\n查詢庫存...\n\n")

        time.sleep(1)  # 等待資料填充

        data = translate(self.trader.req_results)

        # Create a PrettyTable object
        table = PrettyTable()

        # Define the field names (column headers)
        field_names = ['股票代號', '集保庫存（張）', '零股庫存（股）', '融資庫存（張）', '融券庫存（張）']
        table.field_names = field_names

        # Add rows to the table
        for entry in data:
            row = [
                entry['股票代號'],
                str(int(entry['集保庫存股數']) // 1000),
                entry['零股庫存股數'],
                str(int(entry['融券庫存股數']) // 1000),
                str(int(entry['融資庫存股數']) // 1000),
            ]
            table.add_row(row)

        table.align = "c"
        table.align["集保庫存張數"] = "r"
        table.align["零股庫存股數"] = "r"
        table.align["融資庫存張數"] = "r"
        table.align["融券庫存張數"] = "r"

        # Print the table
        print(table)

    # 查詢成交回報
    def get_trade_report(self) -> List[Dict[str, Union[str, int]]]:
        self.api.QryRepDeal(self.account_number)

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
            price=str(price),
            tradingUnit=trading_unit,
            qty=str(qty),
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


handler = AutoTraderX(is_sim=True)

handler.login()
handler.set_order("2330", Side.Buy, 1000, 100, OrderType.IOC)
time.sleep(1)
handler.get_order_report()
# time.sleep(1)
# pprint(translate(handler.trader.req_results))
# breakpoint()

# os.system("pause")
# handler.get_order_report()
# handler.get_trade_report()
handler.stop()
