# AutoTraderX

## 介紹

本專案的目標為實作 Python 自動交易程式，串接目標為元富證券(MasterLink)的 Python API。

由於該公司提供的 API 僅能在 Windows 環境下執行，因此使用者必須具備基於 Windows 的 Python 作業環境。

## 學習資源

- [**股票量化交易從零開始（一）元富證券 API 權限申請**](https://quantpass.org/masterlink-api/)
- [**股票量化交易從零開始（二）Python 環境設置**](https://quantpass.org/masterlink-3/)
- [**股票量化交易從零開始（三）驗證行情與下單權限申請**](https://quantpass.org/masterlink-4/)
- [**股票量化交易從零開始（四）抓取股價歷史資料**](https://quantpass.org/masterlink-5/)
- [**股票量化交易從零開始（五）台股交易策略**](https://quantpass.org/masterlink-6/)

## 安裝必要套件

由於本專案為私有專案，因此只能透過 SSH 協議下載。

請你確保有將自己的 SSH-PubKey 已經新增至 github 帳號，接著：

1. 使用 git clone 下載專案

   ```bash
   git clone git@github.com:DocsaidLab/AutoTraderX.git
   ```

2. 安裝必要套件

   確保你的程式執行環境，根據以下步驟執行。

   - 使用 MiniConda 安裝 Python 環境。

   - 安裝必要 Python 套件：

     ```bash
     pip install ./MasterLink_PythonAPI/MasterTradePy/MasterTradePy/64bit/MasterTradePy-0.0.23-py3-none-win_amd64.whl
     pip install ./MasterLink_PythonAPI/Python_tech_analysis/tech_analysis_api_v2-0.0.5-py3-none-win_amd64.whl
     pip install ./MasterLink_PythonAPI/SolPYAPI/PY_TradeD-0.1.15-py3-none-any.whl
     ```

## 主程式開發紀錄

- 主程式：[`main.py`](./main.py)

- 2024/05/07：

  - PythonAPI 線上下單驗證成功。
  - PythonAPI 報價系統驗證成功。

- 2024/05/11：

  - 新增主程式

    - 重新設計下單操作介面
    - 串接元富證券 API，並且進行登入、登出的測試。
    - 查詢庫存測試：get_inventory()：取得帳戶持股資訊。

  - 懸念：

    - 這個 qid 似乎不是一個即時的回傳結果，必須有 pause 才能看到輸出，這裡之後看要怎麼串接這個回傳結果
    - 目前券商開放的 API 接口有限，庫存的成交明細無法取得，這裡之後要再想辦法
    - 之後得接著看報價系統該如何串接到主程式。

  - 目前可以玩的功能：

    ```python
    handler = AutoTraderX(is_sim=True)

    handler.login()
    handler.get_inventory()
    handler.get_order_report()
    handler.get_trade_report()
    handler.stop()
    ```
