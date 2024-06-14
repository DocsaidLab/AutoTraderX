import time

from src import (QuotationSystem, Trader, divide_into_parts, divide_range,
                 get_curdir, get_files, load_yaml)

DIR = get_curdir(__file__)



def reservation_buy(cfg: dict):
    print(f"\n目標解析: {cfg['name']} {cfg['stock_code']} ...\n")
    print("\t" + "-" * 50)
    time.sleep(SLEEP)

    required_holdings = cfg["required_holdings"]                    # 目標張數
    max_willing_to_pay = cfg["max_willing_to_pay"]                  # 目標價
    order_size_per_transaction = cfg["order_size_per_transaction"]  # 每單交易單位數量

    if (stock_code := cfg['stock_code']) in inventory_data:
        pre_holdings = inventory_data[stock_code]['集保庫存（張）']
    else:
        pre_holdings = 0

    diff_holdings = int(required_holdings) - int(pre_holdings)
    if diff_holdings <= 0:
        status = "不動作"
    else:
        status = "持續買進"

    print(f"\t昨日均價: {pre_avg_price}")
    time.sleep(SLEEP)
    print(f"\t目標價: {max_willing_to_pay}")
    time.sleep(SLEEP)
    print("\t" + "-" * 50)

    print(f"\t昨日庫存: {pre_holdings}")
    time.sleep(SLEEP)
    print(f"\t目標庫存: {required_holdings}")
    time.sleep(SLEEP)
    print("\t" + "-" * 50)
    print(f"\t計算目標差距: {diff_holdings}, 狀態: {status}\n")
    time.sleep(SLEEP)

    # 配置下單
    price_adj = cfg["reservation_buy_price_adjustment"]
    parts = divide_into_parts(diff_holdings, order_size_per_transaction)

    if pre_avg_price < int(max_willing_to_pay):
        # 均價小於目標價，則以均價為標準計算價格
        min_price = pre_avg_price - price_adj
        max_price = pre_avg_price
    else:
        # 均價大於目標價，則以目標價為基準
        min_price = max_willing_to_pay - price_adj
        max_price = max_willing_to_pay

    parts_price, original_price = divide_range(max_price, min_price, len(parts))

    print(f"\t每單數量: {cfg['order_size_per_transaction']}")
    print(f"\t最高價格: {max_price}")
    print(f"\t最低價格: {min_price}")
    print(f"\t價格參數: {price_adj}")
    print("\t" + "-" * 50)
    print(f"\t配置下單: {parts}")
    print(f"\t原始配置價格: {original_price}")
    print(f"\t進位配置價格: {parts_price}\n")
    print("\t" + "-" * 50)
    time.sleep(SLEEP)

    cmd = input("\t輸入(Y/y)，執行下單:")
    if cmd not in ["Y", "y"]:
        pass
        # 執行下單操作


def reservation_sell(cfg):

    print(f"\n目標解析: {cfg['name']} {cfg['stock_code']} ...\n")
    print("\t" + "-" * 50)
    time.sleep(SLEEP)

    order_size_per_transaction = cfg["order_size_per_transaction"]  # 每單交易單位數量

    if (stock_code := cfg['stock_code']) in inventory_data:
        pre_holdings = inventory_data[stock_code]['集保庫存（張）']
    else:
        pre_holdings = 0

    if int(pre_holdings) <= 0:
        status = "不動作"
    else:
        status = "持續賣出"

    print(f"\t昨日庫存: {pre_holdings}")
    time.sleep(SLEEP)
    print(f"\t庫存均價: {pre_holdings}")
    time.sleep(SLEEP)



    # 配置下單
    # price_adj = cfg["reservation_buy_price_adjustment"]
    # parts = divide_into_parts(diff_holdings, order_size_per_transaction)

    # if pre_avg_price < int(max_willing_to_pay):
    #     # 均價小於目標價，則以均價為標準計算價格
    #     min_price = pre_avg_price - price_adj
    #     max_price = pre_avg_price
    # else:
    #     # 均價大於目標價，則以目標價為基準
    #     min_price = max_willing_to_pay - price_adj
    #     max_price = max_willing_to_pay

    # parts_price, original_price = divide_range(max_price, min_price, len(parts))

    # print(f"\t每單數量: {cfg['order_size_per_transaction']}")
    # print(f"\t最高價格: {max_price}")
    # print(f"\t最低價格: {min_price}")
    # print(f"\t價格參數: {price_adj}")
    # print("\t" + "-" * 50)
    # print(f"\t配置下單: {parts}")
    # print(f"\t原始配置價格: {original_price}")
    # print(f"\t進位配置價格: {parts_price}\n")
    # print("\t" + "-" * 50)
    # time.sleep(SLEEP)

    # cmd = input("\t輸入(Y/y)，執行下單:")
    # if cmd not in ["Y", "y"]:
    #     pass
        # 執行下單操作




IS_SIM = False

IS_FORCE = True

IS_EVENT = False

SLEEP = 0.1

# Load account number
# cfg = load_yaml(DIR / "account.yaml")

# Login account
# account = Trader(
#     user=cfg["user"],
#     password=cfg["password"],
#     account_number=str(cfg["account_number"]),
#     is_sim=IS_SIM,
#     is_force=IS_FORCE,
#     is_event=IS_EVENT,
# )

# account.login()
# inventory_data = account.get_inventory()
# time.sleep(1)
# account.stop()

inventory_data = {
    "1101": {
        "股票": "台泥",
        "融券庫存（張）": "0",
        "融資庫存（張）": "0",
        "集保庫存（張）": "1",
        "零股庫存（股）": "0",
    },
    "2002": {
        "股票": "中鋼",
        "融券庫存（張）": "0",
        "融資庫存（張）": "0",
        "集保庫存（張）": "18",
        "零股庫存（股）": "0",
    },
    "3481": {
        "股票": "群創",
        "融券庫存（張）": "0",
        "融資庫存（張）": "0",
        "集保庫存（張）": "24",
        "零股庫存（股）": "0",
    },
    "7566": {
        "股票": "亞果遊艇",
        "融券庫存（張）": "0",
        "融資庫存（張）": "0",
        "集保庫存（張）": "2",
        "零股庫存（股）": "50",
    },
}

# 應計算昨日均價
pre_avg_price = float(18.2)




# Strategy - 非交易時段
fs = get_files(DIR / "subscribed", suffix=[".yaml"])
for f in fs:

    cfg = load_yaml(f)

    if cfg["order_side"] == "Buy":
        print(f"預約單買進\n")
        reservation_buy(cfg)
    elif cfg["order_side"] == "Sell":
        print(f"預約單賣出\n")
        reservation_sell(cfg)






        # breakpoint()


    # self.quotation = QuotationSystem(
    #     user=cfg["user"],
    #     password=cfg["password"],
    #     subscribe_list=["2409", "2884"]
    # )


    # handler.set_order("2330", Side.Buy, 1000, 100, OrderType.IOC)
    # time.sleep(1)

    # pprint(translate(handler.trader.req_results))
    # breakpoint()

    # os.system("pause")
    # handler.get_order_report()
    # handler.get_trade_report()
    # account.stop()
