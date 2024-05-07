# AutoTraderX

## 介紹

本專案的目標為實作 Python 自動交易程式，串接目標為元富證券(MasterLink)的 Python API。

由於該公司提供的 API 僅能在 Windows 環境下執行，因此使用者必須具備基於 Windows 的 Python 作業環境。

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

## 設定交易參數

## 啟動主程式
