[**English**](./README.md) | [中文](./README_tw.md)

# AutoTraderX

<p align="left">
    <a href="./LICENSE"><img src="https://img.shields.io/badge/license-Apache%202-dfd.svg"></a>
    <a href=""><img src="https://img.shields.io/badge/python-3.8+-aff.svg"></a>
</p>

## Introduction

<div align="center">
    <img src="./docs/title.webp" width="800">
</div>

This project mainly integrates with brokerage APIs for automated trading.

## Technical Documentation

For usage and configuration instructions, please refer to the [**AutoTraderX Documents**](https://docsaid.org/en/docs/autotraderx/intro).

## Installation

Currently, there is no installation package available on PyPI, and there are no immediate plans for it.

To use this project, you need to clone it directly from GitHub and install the dependencies.

This project is restricted to use with the MasterLink Python API and operates only on Windows operating systems. Before installation, ensure that you have Python environment set up on Windows.

### Setting Up Python Environment

Refer to our guide for setting up Python on Windows:

- [**Setting up Python Environment on Windows 11**](https://docsaid.org/blog/windows-python-settings)

### Installing AutoTraderX

1. **Clone the project:**

   ```powershell
   git clone https://github.com/DocsaidLab/AutoTraderX.git
   ```

2. **Navigate to the project directory:**

   ```powershell
   cd AutoTraderX
   ```

3. **Install dependencies:**

   ```powershell
   pip install setuptools wheel
   ```

4. **Build the package:**

   ```powershell
   python setup.py bdist_wheel
   ```

5. **Install the package:**

   ```powershell
   pip install dist\autotraderx-*-py3-none-any.whl
   ```

By following these steps, you should successfully install `AutoTraderX`.

### Installing MasterLink Python API

Download the Python API from the MasterLink official website:

- [**MasterLink - Download Area**](https://mlapi.masterlink.com.tw/web_api/service/home#download)

  ![download](./docs/download.jpg)

After downloading, unzip the files and install them using pip:

```powershell
pip install .\MasterTradePy\MasterTradePy\64bit\MasterTradePy-0.0.23-py3-none-win_amd64.whl
pip install .\Python_tech_analysis\tech_analysis_api_v2-0.0.5-py3-none-win_amd64.whl
pip install .\SolPYAPI\PY_TradeD-0.1.15-py3-none-any.whl
```

Once installed, you can use this project.

- **Additional Notes:**

  This project also provides .whl installation files for the MasterLink Python API in the `MasterLink_PythonAPI` folder.

  You can directly run the following command for installation:

  ```powershell
  .\run_install.bat
  ```

  Please note that we do not update these files; please download the latest versions from the MasterLink official website.

## Testing Installation

You can test if the installation was successful with the following command:

```powershell
python -c "import autotraderx; print(autotraderx.__version__)"
# >>> 0.1.0
```

If you see a version number like `0.1.0`, the installation was successful.

## Learning Resources

- [**Quantitative Trading from Scratch (Part 1) - MasterLink API Permission Application**](https://quantpass.org/masterlink-api/)
- [**Quantitative Trading from Scratch (Part 2) - Python Environment Setup**](https://quantpass.org/masterlink-3/)
- [**Quantitative Trading from Scratch (Part 3) - Validating Market Data and Order Permission Application**](https://quantpass.org/masterlink-4/)
- [**Quantitative Trading from Scratch (Part 4) - Fetching Historical Stock Prices**](https://quantpass.org/masterlink-5/)
- [**Quantitative Trading from Scratch (Part 5) - Taiwan Stock Trading Strategies**](https://quantpass.org/masterlink-6/)
- [**e-Certificate Download**](https://www.masterlink.com.tw/certificate-eoperation)

## Citation

```bibtex
@misc{yuan2024autotraderx,
  author = {Ze Yuan},
  title = {AutoTraderX},
  year = {2024},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/DocsaidLab/AutoTraderX}}
}
```
