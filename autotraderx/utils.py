import errno
import json
import math
import os
import time
from enum import Enum
from pathlib import Path
from time import struct_time
from typing import Any, Dict, List, Tuple, Union

import yaml
from natsort import natsorted
from tqdm import tqdm as Tqdm

__all__ = [
    "load_yaml",
    "load_json",
    "dump_json",
    "get_curdir",
    "get_files",
    "COLORSTR",
    "FORMATSTR",
    "colorstr",
    "timestamp2time",
    "time2str",
    "timestamp2str",
    "now",
    "divide_into_parts",
    "divide_range",
]


def get_next_tick_price(price, mode: str = "Buy"):

    thresholds = [
        (10, 0.01),
        (49.95, 0.05),
        (99.9, 0.1),
        (499.5, 0.5),
        (999, 1),
        (float('inf'), 5)  # Handle all prices above 999 inclusively
    ]

    direction = 1 if mode == "Buy" else -1 if mode == "Sell" else None

    if direction is None:
        raise ValueError("Invalid mode. Please use 'Buy' or 'Sell'.")

    if price <= 0:
        raise ValueError("Input price must larger than 0.")

    for limit, change in thresholds:
        if price <= limit:
            return price + (change * direction)

    raise ValueError("Unexpected price value.")


def calc_minimum_profit(
    price: float,
    number: int = 1,
    mode: str = "Buy",
    transaction_tax_percentage: float = 0.003,
    handling_fee_percentage: float = 0.001425,
    discount_percentage: float = 0.6,
    is_day_trading: bool = False
) -> float:
    if mode not in ["Buy", "Sell"]:
        raise ValueError("Input mode must be in ['Buy', 'Sell']")

    day_trading_discount_percentage = 0.5 if is_day_trading else 1

    if mode == "Buy":
        initial_price = price
        buy_handling_fee = math.ceil(price * number * 1000 * handling_fee_percentage * discount_percentage)
        buy_handling_fee = max(buy_handling_fee, 20)

        iteration = 0
        max_iterations = 1000  # Prevent infinite loop

        while iteration < max_iterations:
            price = round(get_next_tick_price(price, mode=mode), 3)
            sell_handling_fee = math.ceil(price * number * 1000 * handling_fee_percentage * discount_percentage)
            sell_handling_fee = max(sell_handling_fee, 20)
            transaction_tax = math.ceil(price * number * 1000 * transaction_tax_percentage * day_trading_discount_percentage)

            profit = (price - initial_price) * number * 1000 - buy_handling_fee - sell_handling_fee - transaction_tax
            if profit > 0:
                break

            iteration += 1

        if iteration == max_iterations:
            raise Exception("Failed to find a profitable price within the max iterations.")

        info = {
            "buy_price": round(initial_price, 3),
            "number": number,
            "buy_handling_fee": buy_handling_fee,
            "sell_handling_fee": sell_handling_fee,
            "transaction_tax": transaction_tax,
            "sell_price": round(price, 3),
            "estimated_profit": int(profit)
        }

        return price, info

    elif mode == "Sell":
        initial_price = price
        sell_handling_fee = math.ceil(price * number * 1000 * handling_fee_percentage * discount_percentage)
        sell_handling_fee = max(sell_handling_fee, 20)
        transaction_tax = math.ceil(price * number * 1000 * transaction_tax_percentage * day_trading_discount_percentage)

        iteration = 0
        max_iterations = 1000  # Prevent infinite loop

        while iteration < max_iterations:
            price = round(get_next_tick_price(price, mode=mode), 3)
            buy_handling_fee = math.ceil(price * number * 1000 * handling_fee_percentage * discount_percentage)
            buy_handling_fee = max(sell_handling_fee, 20)

            profit = (initial_price - price) * number * 1000 - buy_handling_fee - sell_handling_fee - transaction_tax
            if profit > 0:
                break

            iteration += 1

        if iteration == max_iterations:
            raise Exception("Failed to find a profitable price within the max iterations.")

        info = {
            "buy_price": round(initial_price, 3),
            "number": number,
            "buy_handling_fee": buy_handling_fee,
            "sell_handling_fee": sell_handling_fee,
            "transaction_tax": transaction_tax,
            "sell_price": round(price, 3),
            "estimated_profit": int(profit)
        }

        return price, info


def load_yaml(path: Union[Path, str]) -> dict:
    with open(str(path), 'r', encoding='utf-8') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    return data


def load_json(path: Union[Path, str], **kwargs) -> dict:
    with open(str(path), 'r', encoding='utf-8') as f:
        data = json.load(f, **kwargs)
    return data


def dump_json(obj: Any, path: Union[str, Path] = None, **kwargs) -> None:
    dump_options = {
        'sort_keys': False,
        'indent': 2,
        'ensure_ascii': False,
        'escape_forward_slashes': False,
    }
    dump_options.update(kwargs)

    if path is None:
        path = Path.cwd() / 'tmp.json'

    with open(str(path), 'w') as f:
        json.dump(obj, f, **dump_options)


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


def divide_into_parts(A, B):
    result = []
    full_parts = A // B
    remainder = A % B
    for _ in range(full_parts):
        result.append(B)
    if remainder > 0:
        result.append(remainder)
    return result


def round_up_price(price):
    if price < 10:
        # 小於10元，升降單位為0.01元
        return math.ceil(price / 0.01) * 0.01
    elif price < 50:
        # 10元至未滿50元，升降單位為0.05元
        return math.ceil(price / 0.05) * 0.05
    elif price < 100:
        # 50元至未滿100元，升降單位為0.1元
        return math.ceil(price / 0.1) * 0.1
    elif price < 500:
        # 100元至未滿500元，升降單位為0.5元
        return math.ceil(price / 0.5) * 0.5
    elif price < 1000:
        # 500元至未滿1000元，升降單位為1元
        return math.ceil(price / 1.0) * 1.0
    else:
        # 1000元以上，升降單位為5元
        return math.ceil(price / 5.0) * 5.0


def divide_range(A, B, num_parts):
    if num_parts == 1:
        return [A], [A]

    step = (A - B) / (num_parts - 1)
    result, original = [], []
    for i in range(num_parts):
        value = A - step * i
        original.append(round(value, 2))

        value = round_up_price(value)
        result.append(round(value, 2))
    return result, original