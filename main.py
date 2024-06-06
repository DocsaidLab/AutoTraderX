import time

from src import Trader, Stock, get_curdir, load_yaml

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

        self.trader = Trader(
            user=cfg["user"],
            password=cfg["password"],
            account_number=str(cfg["account_number"]),
            is_sim=is_sim,
            is_force=is_force,
            is_event=is_event
        )

        self.stock = Stock(
            user=cfg["user"],
            password=cfg["password"],
        )



handler = AutoTraderX(is_sim=False)

handler.login()
# handler.set_order("2330", Side.Buy, 1000, 100, OrderType.IOC)
# time.sleep(1)
handler.get_inventory()
time.sleep(1)
# pprint(translate(handler.trader.req_results))
# breakpoint()

# os.system("pause")
# handler.get_order_report()
# handler.get_trade_report()
handler.stop()
