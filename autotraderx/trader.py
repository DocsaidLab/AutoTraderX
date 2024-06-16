import time
from typing import Dict, List, Union

from MasterTradePy.api import MasterTradeAPI
from MasterTradePy.constant import (OrderType, PriceType, RCode, Side,
                                    TradingSession, TradingUnit)
from MasterTradePy.model import *
from MasterTradePy.model import (Basic, CrQtyAndDbQty, Inventory, Inventory_S,
                                 MarketTrader, ReportOrder, SecInvQty,
                                 SystemEvent)
from prettytable import PrettyTable

from .utils import dump_json, get_curdir, load_json, now

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


class ConcreteMarketTrader(MarketTrader):

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
        if isinstance(data, ReportOrder):

            report = {
                "tableName": data.order.tableName,
                "ordNo": data.order.ordNo,
                "symbol": data.order.symbol,
                "status": data.order.status,
                "lastMessage": data.lastMessage,
                "lastdealTime": data.order.lastdealTime,
                "orgQty": data.orgOrder.qty,
                "cumQty": data.order.cumQty,
                "dealPri": data.order.dealPri,
                "leavesQty": data.order.leavesQty,
                "price": data.orgOrder.price,
                "trxTime": data.order.trxTime,
                "dealPri": data.order.dealPri,
                "side": data.order.side,
                "priceType": data.order.priceType,
                "orderType": data.order.orderType
            }

            self.reports.append(report)

    def OnReqResult(self, workID: str, data) -> None:
        result = {"workID": workID, "type": type(data).__name__}

        if isinstance(data, Basic):
            result.update({
                "symbol": data.symbol,
                "refPrice": data.refPrice,
                "riseStopPrice": data.riseStopPrice,
                "fallStopPrice": data.fallStopPrice
            })
        elif isinstance(data, Inventory):
            result.update({
                "symbol": data.symbol,
                "qty": data.qty,
                "qtyCredit": data.qtyCredit,
                "qtyDebit": data.qtyDebit,
                "qtyZero": data.qtyZero
            })
        elif isinstance(data, Inventory_S):
            result.update({
                "symbol": data.symbol,
                "qty": data.qty,
                "qtyCredit": data.qtyCredit,
                "qtyDebit": data.qtyDebit,
                "qtyZero": data.qtyZero
            })
        elif isinstance(data, SecInvQty):
            result.update({
                "symbol": data.symbol,
                "secInvQty": data.secInvQty,
                "usedQty": data.usedQty
            })
        elif isinstance(data, CrQtyAndDbQty):
            result.update({
                "symbol": data.Symbol,
                "isCrStop": data.IsCrStop,
                "crQty": data.CrQty,
                "isDbStop": data.IsDbStop,
                "dbQty": data.DbQty,
                "crRate": data.CrRate,
                "dbRate": data.DbRate,
                "canShortUnderUnchanged": data.CanShortUnderUnchanged,
                "dayTrade": data.DayTrade,
                "dayTradeCName": data.DayTradeCName,
                "result": data.result
            })

        self.req_results.append(result)

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
    ):
        self.username = user
        self.password = password
        self.account_number = account_number
        self.is_sim = is_sim
        self.is_force = is_force
        self.is_event = is_event
        self.status = None

        self.stock_info = load_json(DIR / "stock_infos.json")

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

    def process_data(self, data, only_deal: bool = False):
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
        for entry in data:

            price = entry["委託價格"]
            orgQty = entry["委託股數"]
            cumQty = entry["成交股數"]

            # Clean status and message fields
            status = entry['狀態'].split(')')[-1]
            message = entry['訊息'].replace('Tws:48:', '').strip()

            deal_price = ""
            if status == "全部成交":
                deal_price = entry["委託價格"] if entry["成交價格"] == "" else entry["成交價格"]

            if only_deal and status != "全部成交":
                continue

            # Translate table names
            table_name_translation = {
                "RPT:TwsNew": "新訂單",
                "ORD:TwsOrd": "委託訂單",
                "RPT:TwsDeal": "交易報告"
            }
            translated_table_name = table_name_translation.get(
                entry["表格名稱"], entry["表格名稱"])

            # Append processed data into the table
            row = [
                translated_table_name,
                entry["委託書號"],
                self.stock_info[entry['股票代號']]["名稱"],
                entry["股票代號"],
                side_map[entry["買賣別"]],
                price_type_map[entry["委託方式(價格)"]],
                order_type_map[entry["委託方式(效期)"]],
                price,
                orgQty,
                deal_price,
                cumQty,
                status,
                entry["委託時間"],
                entry["成交時間"],
                message
            ]
            table.add_row(row)

            export_data.append({
                "類型": translated_table_name,
                "委託書號": entry["委託書號"],
                "股票": self.stock_info[entry['股票代號']]["名稱"],
                "股票代號": entry["股票代號"],
                "買賣別": side_map[entry["買賣別"]],
                "委託方式(價格)": price_type_map[entry["委託方式(價格)"]],
                "委託方式(效期)": order_type_map[entry["委託方式(效期)"]],
                "委託價": price,
                "委託量": orgQty,
                "成交價": deal_price,
                "成交量": cumQty,
                "狀態": status,
                "委託時間": entry["委託時間"],
                "成交時間": entry["成交時間"],
                "訊息": message
            })

        # Set column alignments
        table.align = "c"
        table.align["委託價"] = "r"
        table.align["委託量"] = "r"
        table.align["成交量"] = "r"

        # Print the table
        print(table)

        return export_data

    # 查詢成交回報
    def get_trade_report(self) -> List[Dict[str, Union[str, int]]]:
        self.api.QryRepDeal(self.account_number)

        print(f"\n\n查詢成交...\n\n")
        time.sleep(1)

        data = translate(self.trader.reports)
        data = self.process_data(data, only_deal=True)
        return data

    # 查詢委託回報
    def get_order_report(self) -> List[Dict[str, Union[str, int]]]:
        self.api.QryRepAll(self.account_number)

        print(f"\n\n查詢委託...\n\n")
        time.sleep(1)

        data = translate(self.trader.reports)
        data = self.process_data(data)
        return data

    # 查詢庫存
    def get_inventory(self) -> List[Dict[str, Union[str, int]]]:
        qid = self.api.ReqInventoryRayinTotal(self.account_number)
        print(f"\n\n查詢庫存...\n\n")

        time.sleep(1)  # 等待資料填充

        data = translate(self.trader.req_results)
        export_data = {}

        # Create a PrettyTable object
        table = PrettyTable()

        # Define the field names (column headers)
        field_names = ['股票', '股票代號', '集保庫存（張）', '零股庫存（股）', '融資庫存（張）', '融券庫存（張）']
        table.field_names = field_names

        # Add rows to the table
        for entry in data:
            row = [
                self.stock_info[entry['股票代號']]["名稱"],
                entry['股票代號'],
                str(int(entry['集保庫存股數']) // 1000),
                entry['零股庫存股數'],
                str(int(entry['融券庫存股數']) // 1000),
                str(int(entry['融資庫存股數']) // 1000),
            ]
            table.add_row(row)

            export_data[entry['股票代號']] = {
                "股票": self.stock_info[entry['股票代號']]["名稱"],
                "集保庫存（張）": str(int(entry['集保庫存股數']) // 1000),
                "零股庫存（股）": entry['零股庫存股數'],
                "融資庫存（張）": str(int(entry['融券庫存股數']) // 1000),
                "融券庫存（張）": str(int(entry['融資庫存股數']) // 1000),
            }

        table.align = "c"
        table.align["集保庫存張數"] = "r"
        table.align["零股庫存股數"] = "r"
        table.align["融資庫存張數"] = "r"
        table.align["融券庫存張數"] = "r"

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
        self.set_order(symbol, Side.BUY, qty * 1000, price)

    def sell(self, symbol: str, qty: int, price: float):
        self.set_order(symbol, Side.SELL, qty * 1000, price)

    def export_deal_infos(self):
        data = self.get_trade_report()
        report = {}
        for d in data:
            if "成交" in d["狀態"]:

                if d["股票代號"] not in report:
                    report[d["股票代號"]] = []

                report[d["股票代號"]].append({
                    "股票": d["股票"],
                    "股票代號": d["股票代號"],
                    "成交時間": now("%Y%m%d")+d["成交時間"],
                    "成交價": d["成交價"],
                    "成交量": d["成交量"],
                    "買賣別": d["買賣別"]
                })

        for k, v in report.items():

            if (fp := DIR / f"deal_info_{k}.json").exists():
                deal_info = load_json(fp)
                deal_info.extend(v)
            else:
                deal_info = v

            dump_json(deal_info, fp)