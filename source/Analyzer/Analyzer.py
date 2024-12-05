from AnalyzerDataTypes import *
import pyxirr

class Analyzer:
    def __init__(self, request: AnalyzerRequest):
        self.request: AnalyzerRequest = request
        self.response_data: dict = dict()
        self.response: AnalyzerResponse

        self.process_request()
        self.send_request()

    def process_request(self):
        if self.request == SharesPortfolioIntervalAnalyzerRequest:
            pass



    def get_cash_flows(self):
        self.cash_flows = dict


