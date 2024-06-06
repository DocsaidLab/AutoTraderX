import errno
import os
import time
from enum import Enum
from pathlib import Path
from time import struct_time
from typing import Any, Dict, List, Tuple, Union

import yaml
from MasterTradePy.model import (Basic, CrQtyAndDbQty, Inventory, Inventory_S,
                                 MarketTrader, ReportOrder, SecInvQty,
                                 SystemEvent)
from natsort import natsorted
from tqdm import tqdm as Tqdm

__all__ = [
    "ConcreteMarketTrader",
    "load_yaml",
    "get_curdir",
    "get_files",
    "COLORSTR",
    "FORMATSTR",
    "colorstr",
    "translate",
    "timestamp2time",
    "time2str",
    "timestamp2str",
    "now",
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
                "details": {}
            }

            if data.order.tableName == "ORD:TwsOrd":
                report["details"] = {
                    "orgQty": data.orgOrder.qty,
                    "cumQty": data.order.cumQty
                }
            elif data.order.tableName == "RPT:TwsDeal":
                report["details"] = {
                    "dealPri": data.order.dealPri,
                    "cumQty": data.order.cumQty,
                    "leavesQty": data.order.leavesQty
                }
            elif data.order.tableName == "RPT:TwsNew":
                report["details"] = {
                    "price": data.orgOrder.price,
                    "orgQty": data.orgOrder.qty
                }
            else:
                report["details"] = {
                    "price": data.orgOrder.price,
                    "orgQty": data.orgOrder.qty,
                    "cumQty": data.order.cumQty
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


def load_yaml(path: Union[Path, str]) -> dict:
    with open(str(path), 'r') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    return data


def get_curdir(
    path: Union[str, Path],
    absolute: bool = True
) -> Path:
    path = Path(path).absolute() if absolute else Path(path)
    return path.parent.resolve()


def get_files(
    folder: Union[str, Path],
    suffix: Union[str, List[str], Tuple[str]] = None,
    recursive: bool = True,
    return_pathlib: bool = True,
    sort_path: bool = True,
    ignore_letter_case: bool = True,
):

    # checking folders
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(
            errno.ENOENT, os.strerror(errno.ENOENT), str(folder))

    if not isinstance(suffix, (str, list, tuple)) and suffix is not None:
        raise TypeError('suffix must be a string, list or tuple.')

    # checking suffix
    suffix = [suffix] if isinstance(suffix, str) else suffix
    if suffix is not None and ignore_letter_case:
        suffix = [s.lower() for s in suffix]

    if recursive:
        files_gen = folder.rglob('*')
    else:
        files_gen = folder.glob('*')

    files = []
    for f in Tqdm(files_gen, leave=False):
        if suffix is None or (ignore_letter_case and f.suffix.lower() in suffix) \
                or (not ignore_letter_case and f.suffix in suffix):
            files.append(f.absolute())

    if not return_pathlib:
        files = [str(f) for f in files]

    if sort_path:
        files = natsorted(files, key=lambda path: str(path).lower())

    return files


class COLORSTR(Enum):
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37
    BRIGHT_BLACK = 90
    BRIGHT_RED = 91
    BRIGHT_GREEN = 92
    BRIGHT_YELLOW = 93
    BRIGHT_BLUE = 94
    BRIGHT_MAGENTA = 95
    BRIGHT_CYAN = 96
    BRIGHT_WHITE = 97


class FORMATSTR(Enum):
    BOLD = 1
    ITALIC = 3
    UNDERLINE = 4


def colorstr(
    obj: Any,
    color: Union[COLORSTR, int, str] = COLORSTR.BLUE,
    fmt: Union[FORMATSTR, int, str] = FORMATSTR.BOLD
) -> str:
    color_code = color.value
    format_code = fmt.value
    color_string = f'\033[{format_code};{color_code}m{obj}\033[0m'
    return color_string


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
        "result": "資券配額查詢結果"
    }

    return [
        {
            key_mapping_table[k]: v
            for k, v in d.items()
        } for d in data
    ]


def timestamp2time(ts: Union[int, float]):
    return time.localtime(ts)


def time2str(t: struct_time, fmt: str):
    if not isinstance(t, struct_time):
        raise TypeError(f'Input type: {type(t)} error.')
    return time.strftime(fmt, t)


def timestamp2str(ts: Union[int, float], fmt: str):
    return time2str(timestamp2time(ts), fmt)


def now(fmt: str = None):
    t = time.time()
    t = timestamp2str(time.time(), fmt=fmt)
    return t