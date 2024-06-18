import time
from typing import Dict, List, Union

from MasterTradePy.api import MasterTradeAPI
from MasterTradePy.constant import (OrderType, PriceType, RCode, Side,
                                    TradingSession, TradingUnit)
from MasterTradePy.model import *
from MasterTradePy.model import MarketTrader, SystemEvent
from prettytable import PrettyTable

from .utils import get_curdir, load_json

DIR = get_curdir(__file__)



def translate(data: Dict[str, Union[str, int]]) -> Dict[str, Union[str, int]]:

    key_mapping_table = {
        "tableName": "表格名稱",
        "ordNo": "委託書號",
        "symbol": "股票代號",
        "status": "狀態",
        "lastMessage": "訊息",
        "details": "詳細資料",
        "orgQty": "委託股數",
        "cumQty": "成交股數",
        "dealPri": "成交價格",
        "leavesQty": "剩餘股數",
        "price": "委託價格",
        "workID": "工作編號",
        "type": "類型",
        "refPrice": "參考價",
        "riseStopPrice": "漲停價",
        "fallStopPrice": "跌停價",
        "qty": "集保庫存股數",
        "qtyCredit": "融資庫存股數",
        "qtyDebit": "融券庫存股數",
        "qtyZero": "零股庫存股數",
        "secInvQty": "總券源股數",
        "usedQty": "以使用股數",
        "isCrStop": "是否停資",
        "crQty": "融資配額股數",
        "isDbStop": "是否停券",
        "dbQty": "融券配額股數",
        "crRate": "資成數",
        "dbRate": "券成數",
        "canShortUnderUnchanged": "平盤下是否可下券",
        "dayTrade": "是否可當沖",
        "dayTradeCName": "是否可當沖(中文)",
        "result": "資券配額查詢結果",
        "trxTime": "委託時間",
        "lastdealTime": "成交時間",
        "priceType": "委託方式(價格)",
        "orderType": "委託方式(效期)",
        "side": "買賣別"
    }

    return [
        {
            key_mapping_table[k]: v
            for k, v in d.items()
        } for d in data
    ]


class CustomMarketTrader(MarketTrader):

    def __init__(self):
        self.new_order_replies = []
        self.change_replies = []
        self.cancel_replies = []
        self.reports = []
        self.req_results = []
        self.system_events = []
        self.announcement_events = []
        self.errors = []

    def OnNewOrderReply(self, data) -> None:
        self.new_order_replies.append(data)

    def OnChangeReply(self, data) -> None:
        self.change_replies.append(data)

    def OnCancelReply(self, data) -> None:
        self.cancel_replies.append(data)

    def OnReport(self, data) -> None:
        self.reports.append(data)

    def OnReqResult(self, workID: str, data) -> None:
        self.req_results.append(data)

    def OnSystemEvent(self, data: SystemEvent) -> None:
        self.system_events.append(data)

    def OnAnnouncementEvent(self, data) -> None:
        self.announcement_events.append(data)

    def OnError(self, data):
        self.errors.append(data)


class Trader:

    def __init__(
        self,
        user: str,
        password: str,
        account_number: str,
        is_sim: bool = True,    # 是否連測試主機
        is_force: bool = True,  # 是否單一帳號通過強制登入
        is_event: bool = False,  # 是否連接競賽主機
        verbose: bool = True # 是否輸出資訊至 cmd
    ):
        self.username = user
        self.password = password
        self.account_number = account_number
        self.is_sim = is_sim
        self.is_force = is_force
        self.is_event = is_event
        self.verbose = verbose
        self.status = None
        self.stock_info = load_json(DIR / "stock_infos.json")

    def login(self):
        self.trader = CustomMarketTrader()
        self.api = MasterTradeAPI(self.trader)
        self.api.SetConnectionHost('solace140.masterlink.com.tw:55555')
        rc = self.api.Login(
            self.username,
            self.password,
            self.is_sim,
            self.is_force,
            self.is_event
        )
        if rc != RCode.OK:
            print("登入失敗，請檢查使用者名稱和密碼是否正確")
        self.status = True

    def stop(self):
        self.api.disClient()
        self.status = False

    # 查詢成交回報
    def get_trade_report(self) -> List[Dict[str, Union[str, int]]]:
        self.api.QryRepDeal(self.account_number)
        print(f"\n\n查詢成交...\n\n")
        time.sleep(1)
        return self.process_data(self.trader.reports, only_deal=True)

    # 查詢委託回報
    def get_order_report(self) -> List[Dict[str, Union[str, int]]]:
        self.api.QryRepAll(self.account_number)
        print(f"\n\n查詢委託...\n\n")
        time.sleep(1)
        return self.process_data(self.trader.reports)

    def process_data(self, trader_reports, only_deal: bool = False):
        export_data = []

        # Create a PrettyTable object
        table = PrettyTable()

        # Customizing the table headers based on data needs
        table.field_names = [
            "類型", "委託書號", "股票", "股票代號", "買賣別",
            "委託方式(價格)", "委託方式(效期)", "委託價", "委託量",
            "成交價", "成交量", "狀態", "委託時間", "成交時間", "訊息"
        ]

        side_map = {
            "S": "Sell",
            "B": "Buy"
        }

        order_type_map = {
            "R": "當日有效",
            "I": "立即成交，否則取消",
            "F": "立即全部成交，否則取消"
        }

        price_type_map = {
            "L": "限價單",
            "M": "市價單"
        }

        # Add rows to the table after processing detail data
        for data in trader_reports:

            if only_deal and "全部成交" not in data.order.status:
                continue

            # Translate table names
            table_name_translation = {
                "RPT:TwsNew": "新訂單",
                "ORD:TwsOrd": "委託訂單",
                "RPT:TwsDeal": "交易報告"
            }
            translated_table_name = table_name_translation[data.order.tableName]

            # Append processed data into the table
            row = [
                translated_table_name,
                data.order.ordNo,
                self.stock_info[data.order.symbol]["名稱"],
                data.order.symbol,
                side_map[data.order.side],
                price_type_map[data.order.priceType],
                order_type_map[data.order.orderType],
                data.orgOrder.price,
                data.orgOrder.qty,
                data.order.dealPri,
                data.order.cumQty,
                data.order.status.split(')')[-1],
                data.order.trxTime,
                data.order.lastdealTime,
                data.lastMessage.replace('Tws:48:', '').strip()
            ]
            table.add_row(row)

            export_data.append({
                "類型": translated_table_name,
                "委託書號": data.order.ordNo,
                "股票": self.stock_info[data.order.symbol]["名稱"],
                "股票代號": data.order.symbol,
                "買賣別": side_map[data.order.side],
                "委託方式(價格)": price_type_map[data.order.priceType],
                "委託方式(效期)": order_type_map[data.order.orderType],
                "委託價": data.orgOrder.price,
                "委託量": data.orgOrder.qty,
                "成交價": data.order.dealPri,
                "成交量": data.order.cumQty,
                "狀態": data.order.status,
                "委託時間": data.order.trxTime,
                "成交時間": data.order.lastdealTime,
                "訊息": data.lastMessage
            })

        # Set column alignments
        table.align = "c"
        table.align["委託價"] = "r"
        table.align["委託量"] = "r"
        table.align["成交量"] = "r"

        if self.verbose:
            # Print the table
            print(table)
            print('\n')

        return export_data

    # 查詢庫存
    def get_inventory(self) -> List[Dict[str, Union[str, int]]]:
        self.api.ReqInventoryRayinTotal(self.account_number)
        print(f"\n\n查詢庫存...\n\n")
        time.sleep(1)  # 等待資料填充

        # Create a PrettyTable object
        table = PrettyTable()
        export_data = {}

        # Define the field names (column headers)
        field_names = ['股票', '股票代號', '集保庫存（張）', '零股庫存（股）', '融資庫存（張）', '融券庫存（張）']
        table.field_names = field_names

        # Add rows to the table
        for data in self.trader.req_results:
            row = [
                self.stock_info[data.symbol]["名稱"],
                data.symbol,
                str(int(data.qty) // 1000),
                data.qtyZero,
                str(int(data.qtyCredit) // 1000),
                str(int(data.qtyDebit) // 1000),
            ]
            table.add_row(row)

            export_data[data.symbol] = {
                "股票": self.stock_info[data.symbol]["名稱"],
                "集保庫存（張）": str(int(data.qty) // 1000),
                "零股庫存（股）": data.qtyZero,
                "融資庫存（張）": str(int(data.qtyCredit) // 1000),
                "融券庫存（張）": str(int(data.qtyDebit) // 1000),
            }

        table.align = "c"
        table.align["集保庫存張數"] = "r"
        table.align["零股庫存股數"] = "r"
        table.align["融資庫存張數"] = "r"
        table.align["融券庫存張數"] = "r"

        if self.verbose:
            # Print the table
            print(table)

        return export_data

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
        self.set_order(symbol, Side.Buy, qty * 1000, price)

    def sell(self, symbol: str, qty: int, price: float):
        self.set_order(symbol, Side.Sell, qty * 1000, price)

    def change_price(self, order_number: str, mod_price: float):
        replaceOrder = OrderPriceChange(
            ordNo=order_number,
            price=str(mod_price),
            tradingAccount=self.account_number
        )
        rcode = self.api.ChangeOrderPrice(replaceOrder)
        if rcode == RCode.OK:
            print(u'已送出委託')
        else:
            print(u'改價失敗! 請再次執行程式，依據回報資料修正輸入')

    def change_qty(self, order_number, mod_qty: int):
        replaceOrder = OrderQtyChange(
            ordNo=order_number,
            qty=str(mod_qty),
            tradingAccount=self.account_number
        )
        rcode = self.api.ChangeOrderQty(replaceOrder)
        if rcode == RCode.OK:
            print(u'已送出委託')
        else:
            print(u'改量失敗! 請再次執行程式，依據回報資料修正輸入')