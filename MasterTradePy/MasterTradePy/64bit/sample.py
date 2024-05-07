import sys
from MasterTradePy.api import MasterTradeAPI
# from MasterTradePy.model import Basic, MarketTrader, Order, OrderQtyChange, OrderPriceChange, ReportOrder, SystemEvent, Inventory
from MasterTradePy.model import *
from MasterTradePy.constant import Config, Exchange, PriceType, OrderType, TradingSession, Side, TradingUnit
from MasterTradePy.helper import Helper
from MasterTradePy.constant import RCode
from MasterTradePy.soclient import SolClient, ServiceEventHandler, TradeMessageHandler
from MasterTradePy.utils import log
import os

def Options(pisSim:bool = False):
    while True:
        if pisSim:
            cmd = input('0: 結束\n1: 下單\n2: 改量\n3: 改價\n4: 查詢委託回報\n5: 查詢成交回報\n')            
        else:
            cmd = input('0: 結束\n1: 下單\n2: 改量\n3: 改價\n4: 查詢委託回報\n5: 查詢成交回報\n6: 期初庫存\n7: 庫存\n8: 或有券源\n9: 資券配額\n')
            
        if cmd == '0':
            api.disClient()
            os.system("pause")
            sys.exit(0)
        elif cmd == '1':#下單
            symbol = input(u'請輸入欲買進股票代號:')
            api.ReqBasic(symbol)
            account = input(u'請輸入下單帳號:')
            price = input(u'請輸入欲買進股票價格(空白表示市價下單):')
            qty = input(u'請輸入欲買進股票股數(1張請輸入1000):')
            orderTypeSymbol = input(u'請輸入類別(I:IOC, F:FOK, 其他:ROD):')
            
            orderType = OrderType.ROD
            if orderTypeSymbol == 'I':
                orderType = OrderType.IOC
            elif orderTypeSymbol == 'F':
                orderType = OrderType.FOK

            if not price:
                priceType = PriceType.MKT
            else:
                priceType = PriceType.LMT

            order = Order(tradingSession=TradingSession.NORMAL,
                        side=Side.Buy,
                        symbol=symbol,
                        priceType=priceType,
                        price=price,
                        tradingUnit=TradingUnit.COMMON, 
                        qty=qty,
                        orderType=orderType,
                        tradingAccount=account,
                        userDef='')
            rcode = api.NewOrder(order)
            if rcode == RCode.OK:
                print(u'已送出委託')
            else:
                print(u'下單失敗! 請再次執行程式，依據回報資料修正輸入')

        elif cmd == '2':#改量
            ordNo = input(u'請輸入單號:')
            account = input(u'請輸入下單帳號:')
            qty = input(u'請輸入股票股數(1張請輸入1000):')
            
            replaceOrder = OrderQtyChange(ordNo=ordNo,
                        qty = qty,
                        tradingAccount=account)

            rcode = api.ChangeOrderQty(replaceOrder)
            if rcode == RCode.OK:
                print(u'已送出委託')
            else:
                print(u'改量失敗! 請再次執行程式，依據回報資料修正輸入')

        elif cmd == '3':#改價
            ordNo = input(u'請輸入單號:')
            account = input(u'請輸入下單帳號:')
            price = input(u'請輸入股票價格(空白表示市價下單):')
            
            replaceOrder = OrderPriceChange(ordNo=ordNo,
                        price = price,
                        tradingAccount=account)

            rcode = api.ChangeOrderPrice(replaceOrder)
            if rcode == RCode.OK:
                print(u'已送出委託')
            else:
                print(u'改價失敗! 請再次執行程式，依據回報資料修正輸入')
        elif cmd == '4':#查詢委託回報
            account = input(u'請輸入下單帳號:')
            api.QryRepAll(account)
        elif cmd == '5':#查詢成交回報
            account = input(u'請輸入下單帳號:')
            api.QryRepDeal(account)
        elif cmd == '6':#期初庫存
            account = input(u'請輸入下單帳號:')
            qid = api.ReqInventoryOpen(account)
            print(f'qid: {qid}')
        elif cmd == '7':#庫存
            account = input(u'請輸入下單帳號:')
            qid = api.ReqInventoryRayinTotal(account)
            print(f'qid: {qid}')        
        elif cmd == '8':#或有券源
            account = input(u'請輸入下單帳號:')
            symbol = input(u'請輸入委託代碼:')
            qid = api.QrySecInvQty_Rayin(account, symbol)
        elif cmd == '9':#資券配額
            account = input(u'請輸入下單帳號:')
            symbol = input(u'請輸入委託代碼:')
            qid = api.QryProdCrQty_Rayin(account, symbol)           


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
    TReqStep_DupFinished = '91'         #重複的[結束]回報,例如:報價單,先收到Bid成交,再收到Offer成功,此時Offer成功的回報就是TReqStep_DupFinished
    TReqStep_UnknownFail = '95'         #委託要求狀態不明(例如:送出後斷線)
    TReqStep_Reject = '99'              #委託要求拒絕
    TReqStep_RptSuggestNew = '100'      #先收到成交回報,所建立的新單(遺漏正常新單回報)
    TReqStep_RptPartFilled = '110'      #配合 TReqKind_RptFilled: 部份成交
    TReqStep_RptFullFilled = '111'      #配合 TReqKind_RptFilled: 全部成交
    TReqStep_RptExchgKilled = '120'     #委託因IOC/FOK未成交而取消

    TOrderSt_NewPending = TReqStep_Pending             #尚未處理
    TOrderSt_Force = TReqStep_BackConfirm              #新單要求退回給使用者(或營業主管)確定or強迫
    TOrderSt_NewQueuing = TReqStep_Queuing             #新單排隊中
    TOrderSt_NewSending = TReqStep_Sending             #新單傳送中
    TOrderSt_Sent = TReqStep_Sent                      #新單已送出(等回報)
    TOrderSt_InternalCanceling ='81'                   #內部刪除 [其他主機 NewQueuing] 的委託.
    TOrderSt_InternalCanceled ='91'                    #新單尚未送出就被刪單
    TOrderSt_NewUnknownFail = TReqStep_UnknownFail     #新單要求狀態不明(例如:送出後斷線)
    TOrderSt_NewReject = TReqStep_Reject               #新單要求拒絕
    TOrderSt_Accepted = '101'                          #委託已接受(交易所已接受)
    TOrderSt_PartFilled = TReqStep_RptPartFilled       #部份成交
    TOrderSt_FullFilled = TReqStep_RptFullFilled       #全部成交
    TOrderSt_IOCFOKNotFilled = TReqStep_RptExchgKilled #一般:委託因IOC/FOK未成交而取消.報價:時間到自動刪單,有新報價舊報價自動刪單.
    TOrderSt_ExchgKilled = TOrderSt_IOCFOKNotFilled
        """
        if type(data) is ReportOrder:
            # 回報資料
            print(data.order.tableName)
            if data.order.tableName == "ORD:TwsOrd":
                print(f'回報資料: 委託書號={data.order.ordNo}, 股票代號={data.order.symbol}, 委託股數={data.orgOrder.qty}, 成交股數={data.order.cumQty}, 訊息={data.lastMessage}, 狀態={data.order.status}')
            elif data.order.tableName == "RPT:TwsDeal":
                print(f'回報資料: 委託書號={data.order.ordNo}, 股票代號={data.order.symbol}, 成交價格={data.order.dealPri}, 成交股數={data.order.cumQty}, 剩餘股數={data.order.leavesQty} 訊息={data.lastMessage}, 狀態={data.order.status}')
            elif data.order.tableName == "RPT:TwsNew":
                print(f'回報資料: 委託書號={data.order.ordNo}, 股票代號={data.order.symbol}, 委託價格={data.orgOrder.price}, 委託股數={data.orgOrder.qty}, 訊息={data.lastMessage}, 狀態={data.order.status}')
            else:
                print(f'回報資料: 委託書號={data.order.ordNo}, 股票代號={data.order.symbol}, 委託價格={data.orgOrder.price}, 委託股數={data.orgOrder.qty}, 成交股數={data.order.cumQty}, 訊息={data.lastMessage}, 狀態={data.order.status}')
    
    def OnReqResult(self, workID: str, data) -> None:
        if type(data) is Basic:# 基本資料            
            print(f'workid={workID}, 證券基本資料: 股票代號={data.symbol}, 參考價={data.refPrice}, 漲停價={data.riseStopPrice}, 跌停價={data.fallStopPrice}')
        if type(data) is Inventory:# 庫存資料            
            print(f'workid={workID}, 庫存資料:商品代碼:{data.symbol}, 集保庫存股數:{data.qty}, 融資庫存股數:{data.qtyCredit}, 融券庫存股數:{data.qtyDebit}, 零股庫存股數:{data.qtyZero}')
        if type(data) is Inventory_S:# 期初庫存資料            
            print(f'workid={workID}, 期初庫存資料:商品代碼:{data.symbol}, 集保庫存股數:{data.qty}, 融資庫存股數:{data.qtyCredit}, 融券庫存股數:{data.qtyDebit}, 零股庫存股數:{data.qtyZero}')
        if type(data) is SecInvQty:#或有券源
            print(f'workid={workID}, 或有券源:商品代碼={data.symbol}, 總券源股數={data.secInvQty}, 以使用股數={data.usedQty}')
        if type(data) is CrQtyAndDbQty:#資券配額
            print(f'workid={workID}, 資券配額:商品代碼={data.Symbol}, 是否停資={data.IsCrStop}, 融資配額股數={data.CrQty}, 是否停券={data.IsDbStop}, 融券配額股數={data.DbQty}, 資成數={data.CrRate}, 券成數={data.DbRate}, 平盤下是否可下券={data.CanShortUnderUnchanged}, 是否可當沖:{data.DayTrade}, 是否可當沖(中文):{data.DayTradeCName}, 資券配額查詢結果={data.result}')
            # print(f'workid={workID}, 資券配額:{data}')

    def OnSystemEvent(self, data: SystemEvent) -> None:
        print(f'OnSystemEvent{data}')
    
    def OnAnnouncementEvent(self, data)->None:
        print(f'OnAnnouncementEvent:{data}')
                  
    def OnError(self, data):
        print(data)

if __name__ == '__main__':
    if len(sys.argv) < 6:
        print('args: {使用者名稱} {密碼} {是否連測試(True/False)} {是否單一帳號通過強制登入(True/False)} {是否連接競賽主機(True/False)}\n')
        os.system("pause")

    is_64bits = sys.maxsize > 2**32
    if not is_64bits:
        print("執行版本錯誤,請使用python-64bit版本")
        os.system("pause")
        sys.exit(0)
    username = sys.argv[1]
    password = sys.argv[2]   

    is_sim = True
    if sys.argv[3] == 'False':
        is_sim = False
    is_force = True
    if sys.argv[4] == 'False':
        is_force = False
    is_event = False
    if sys.argv[5] == 'True':
        is_event = True

    trader = ConcreteMarketTrader()
    api = MasterTradeAPI(trader)
    api.SetConnectionHost('solace140.masterlink.com.tw:55555')
    rc = api.Login(username, password, is_sim, is_force, is_event)
    if rc == RCode.OK or rc == RCode.USER_NOT_VERIFIED or rc == RCode.PART_USER_VERIFIED:
        if not is_sim and rc != RCode.OK :
            print(u'帳號未驗證\n')
            os.system("pause")
            sys.exit(0)
        else:
            print(u'交易主機連線成功，進行雙因子認證\n')
        # 雙因子認證
        accounts = [x[4:] for x in api.accounts]
        rcc = api.CheckAccs(tradingAccounts=accounts)
        cmd = ''
        if rcc != RCode.OK:
            print(u'雙因子驗證不通過 請洽客服人員\n')
            os.system("pause")
            sys.exit(0)
        
        if rc == RCode.OK:
            print(u'驗證已通過 可執行API交易功能\n')
            Options(is_sim)
            
        if rc == RCode.PART_USER_VERIFIED and is_force:
            print(u'驗證部分已通過 可執行API交易功能\n')
            Options(is_sim)
            
        elif rc == RCode.USER_NOT_VERIFIED:
            print(u'帳號未驗證\n')
            Options(is_sim)

    else:
        print(u'驗證不通過 請洽客服人員\n')
        os.system("pause")
        sys.exit(0)