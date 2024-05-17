import errno
import os
import time
from datetime import datetime
from enum import Enum, IntEnum
from pathlib import Path
from time import struct_time
from typing import Any, List, Tuple, Union

import yaml
from MasterTradePy.model import (Basic, CrQtyAndDbQty, Inventory, Inventory_S,
                                 MarketTrader, ReportOrder, SecInvQty,
                                 SystemEvent)
from natsort import natsorted
from tqdm import tqdm as Tqdm


class ConcreteMarketTrader(MarketTrader):

    def OnNewOrderReply(self, data) -> None:
        print(data)

    def OnChangeReply(self, data) -> None:
        print(data)

    def OnCancelReply(self, data) -> None:
        print(data)

    def OnReport(self, data) -> None:
        """
        TReqStep_Pending ='0'               #委託要求處理中
        TReqStep_BackConfirm = '3'          #本機委託要求退回給使用者(或營業主管)確定or強迫
        TReqStep_Queuing = '5'              #本機委託要求排隊中
        TReqStep_Sending = '6'              #本機委託要求傳送中
        TReqStep_Sent = '7'                 #本機委託要求已送出(等回報)
        TReqStep_PartReject = '88'          #部份結束(失敗):例如:收到報價單的Bid失敗,Offer尚未回覆
        TReqStep_PartFinish = '89'          #部份結束:例如收到報價單的其中一邊,還缺另一邊
        TReqStep_Finished = '90'            #委託要求已結束
        #重複的[結束]回報,例如:報價單,先收到Bid成交,再收到Offer成功,此時Offer成功的回報就是TReqStep_DupFinished
        TReqStep_DupFinished = '91'
        TReqStep_UnknownFail = '95'         #委託要求狀態不明(例如:送出後斷線)
        TReqStep_Reject = '99'              #委託要求拒絕
        TReqStep_RptSuggestNew = '100'      #先收到成交回報,所建立的新單(遺漏正常新單回報)
        TReqStep_RptPartFilled = '110'      #配合 TReqKind_RptFilled: 部份成交
        TReqStep_RptFullFilled = '111'      #配合 TReqKind_RptFilled: 全部成交
        TReqStep_RptExchgKilled = '120'     #委託因IOC/FOK未成交而取消

        TOrderSt_NewPending = TReqStep_Pending             #尚未處理
        #新單要求退回給使用者(或營業主管)確定or強迫
        TOrderSt_Force = TReqStep_BackConfirm
        TOrderSt_NewQueuing = TReqStep_Queuing             #新單排隊中
        TOrderSt_NewSending = TReqStep_Sending             #新單傳送中
        TOrderSt_Sent = TReqStep_Sent                      #新單已送出(等回報)
        #內部刪除 [其他主機 NewQueuing] 的委託.
        TOrderSt_InternalCanceling ='81'
        TOrderSt_InternalCanceled ='91'                    #新單尚未送出就被刪單
        TOrderSt_NewUnknownFail = TReqStep_UnknownFail     #新單要求狀態不明(例如:送出後斷線)
        TOrderSt_NewReject = TReqStep_Reject               #新單要求拒絕
        TOrderSt_Accepted = '101'                          #委託已接受(交易所已接受)
        TOrderSt_PartFilled = TReqStep_RptPartFilled       #部份成交
        TOrderSt_FullFilled = TReqStep_RptFullFilled       #全部成交
        #一般:委託因IOC/FOK未成交而取消.報價:時間到自動刪單,有新報價舊報價自動刪單.
        TOrderSt_IOCFOKNotFilled = TReqStep_RptExchgKilled
        TOrderSt_ExchgKilled = TOrderSt_IOCFOKNotFilled
        """
        if type(data) is ReportOrder:
            # 回報資料
            print(data.order.tableName)
            if data.order.tableName == "ORD:TwsOrd":
                print(
                    f'回報資料: 委託書號={data.order.ordNo}, 股票代號={data.order.symbol}, 委託股數={data.orgOrder.qty}, 成交股數={data.order.cumQty}, 訊息={data.lastMessage}, 狀態={data.order.status}')
            elif data.order.tableName == "RPT:TwsDeal":
                print(f'回報資料: 委託書號={data.order.ordNo}, 股票代號={data.order.symbol}, 成交價格={data.order.dealPri}, 成交股數={
                      data.order.cumQty}, 剩餘股數={data.order.leavesQty} 訊息={data.lastMessage}, 狀態={data.order.status}')
            elif data.order.tableName == "RPT:TwsNew":
                print(
                    f'回報資料: 委託書號={data.order.ordNo}, 股票代號={data.order.symbol}, 委託價格={data.orgOrder.price}, 委託股數={data.orgOrder.qty}, 訊息={data.lastMessage}, 狀態={data.order.status}')
            else:
                print(f'回報資料: 委託書號={data.order.ordNo}, 股票代號={data.order.symbol}, 委託價格={data.orgOrder.price}, 委託股數={
                      data.orgOrder.qty}, 成交股數={data.order.cumQty}, 訊息={data.lastMessage}, 狀態={data.order.status}')

    def OnReqResult(self, workID: str, data) -> None:
        if type(data) is Basic:  # 基本資料
            print(
                f'workid={workID}, 證券基本資料: 股票代號={data.symbol}, 參考價={data.refPrice}, 漲停價={data.riseStopPrice}, 跌停價={data.fallStopPrice}')
        if type(data) is Inventory:  # 庫存資料
            print(
                f'workid={workID}, 庫存資料:商品代碼:{data.symbol}, 集保庫存股數:{data.qty}, 融資庫存股數:{data.qtyCredit}, 融券庫存股數:{data.qtyDebit}, 零股庫存股數:{data.qtyZero}')
        if type(data) is Inventory_S:  # 期初庫存資料
            print(
                f'workid={workID}, 期初庫存資料:商品代碼:{data.symbol}, 集保庫存股數:{data.qty}, 融資庫存股數:{data.qtyCredit}, 融券庫存股數:{data.qtyDebit}, 零股庫存股數:{data.qtyZero}')
        if type(data) is SecInvQty:  # 或有券源
            print(
                f'workid={workID}, 或有券源:商品代碼={data.symbol}, 總券源股數={data.secInvQty}, 以使用股數={data.usedQty}')
        if type(data) is CrQtyAndDbQty:  # 資券配額
            print(f'workid={workID}, 資券配額:商品代碼={data.Symbol}, 是否停資={data.IsCrStop}, 融資配額股數={data.CrQty}, 是否停券={data.IsDbStop}, 融券配額股數={data.DbQty}, 資成數={
                  data.CrRate}, 券成數={data.DbRate}, 平盤下是否可下券={data.CanShortUnderUnchanged}, 是否可當沖:{data.DayTrade}, 是否可當沖(中文):{data.DayTradeCName}, 資券配額查詢結果={data.result}')
            # print(f'workid={workID}, 資券配額:{data}')

    def OnSystemEvent(self, data: SystemEvent) -> None:
        print(f'OnSystemEvent{data}')

    def OnAnnouncementEvent(self, data) -> None:
        print(f'OnAnnouncementEvent:{data}')

    def OnError(self, data):
        print(data)


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
    """
    This function is make colorful string for python.

    Args:
        obj (Any): The object you want to make it print colorful.
        color (Union[COLORSTR, int, str], optional):
            The print color of obj. Defaults to COLORSTR.BLUE.
        fmt (Union[FORMATSTR, int, str], optional):
            The print format of obj. Defaults to FORMATSTR.BOLD.
            Options = {
                'bold', 'underline'
            }

    Returns:
        string: color string.
    """
    color_code = color.value
    format_code = fmt.value
    color_string = f'\033[{format_code};{color_code}m{obj}\033[0m'
    return color_string
