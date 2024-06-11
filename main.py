import time

from src import Account, get_curdir, load_yaml, QuotationSystem

DIR = get_curdir(__file__)

IS_SIM = False

IS_FORCE = True

IS_EVENT = False

# Load account number
cfg = load_yaml(DIR / "account.yaml")

# Login account
account = Account(
    user=cfg["user"],
    password=cfg["password"],
    account_number=str(cfg["account_number"]),
    is_sim=IS_SIM,
    is_force=IS_FORCE,
    is_event=IS_EVENT
)

account.login()

# self.quotation = QuotationSystem(
#     user=cfg["user"],
#     password=cfg["password"],
#     subscribe_list=["2409", "2884"]
# )




# handler.set_order("2330", Side.Buy, 1000, 100, OrderType.IOC)
# time.sleep(1)
account.get_inventory()
time.sleep(1)
# pprint(translate(handler.trader.req_results))
# breakpoint()

# os.system("pause")
# handler.get_order_report()
# handler.get_trade_report()
account.stop()
