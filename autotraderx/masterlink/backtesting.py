import threading

from tech_analysis_api_v2.api import TechAnalysis
from tech_analysis_api_v2.model import *

event = threading.Event()


def OnDigitalSSOEvent(aIsOK, aMsg):
    print(f'OnDigitalSSOEvent: {aIsOK} {aMsg}')


def OnTAConnStuEvent(aIsOK):
    print(f'OnTAConnStuEvent: {aIsOK}')
    if aIsOK:
        event.set()


class BackTesting:

    def __init__(
        self,
        user: str,
        password: str,
    ):
        self.user = user
        self.password = password
        self.tech_analysis = TechAnalysis(OnDigitalSSOEvent, OnTAConnStuEvent, None, None)
        self.tech_analysis.Login(self.user, self.password)
        event.wait()

    def get_data(self, prod_id: str, date: str):
        _data, err_msg = self.tech_analysis.GetHisBS_Stock(prod_id, date)

        if err_msg != "":
            print(err_msg)
            return []

        data = [
            {
                "股票代號": d.Prod,
                "成交時間": d.Match_Time,
                "成交價格": d.Match_Price,
                "成交量": d.Match_Quantity,
                "試搓": d.Is_TryMatch,
                "買賣": d.BS
            } for d in _data
        ]

        return data
