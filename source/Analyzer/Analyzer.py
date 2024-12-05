from AnalyzerDataTypes import *
import pyxirr
from collections import defaultdict
import datetime
import copy


class Analyzer:
    def __init__(self, request: AnalyzerRequest):
        self.request: AnalyzerRequest = request
        self.response_data: dict = dict()
        self.response: AnalyzerResponse
        self.begin_portfolio: dict[InstrumentType, defaultdict[str, int]] = dict()
        self.end_portfolio: dict[InstrumentType, defaultdict[str, int]] = dict()
        self.all_cash_flows: dict[InstrumentType, list[tuple[datetime, float]]] = dict()
        self.instruments_cash_flow: dict[InstrumentType, dict[str, float]] = dict()
        self.first_period_op_ind: int = 0

        for t in InstrumentType:
            self.begin_portfolio[t] = defaultdict(int)
            self.end_portfolio[t] = defaultdict(int)
            self.all_cash_flows[t] = []

        self.process_request()
        self.send_response()

    def process_request(self):
        if isinstance(self.request, SharesPortfolioIntervalAnalyzerRequest):
            self.get_begin_end_dates_portfolio()
            self.get_cash_flows()

    def get_begin_end_dates_portfolio(self):
        before_begin = True
        for ind, op in enumerate(self.request.operations):
            if before_begin:
                if op.date.replace(tzinfo=None) > self.request.begin_date:
                    before_begin = False
                    self.first_period_op_ind = ind
                    self.end_portfolio = copy.deepcopy(self.begin_portfolio)
                    break
                if op.operation_type == OperationType.BUY:
                    self.begin_portfolio[op.instrument_type][op.figi] += op.quantity
                else:
                    self.begin_portfolio[op.instrument_type][op.figi] -= op.quantity
        for op in self.request.operations[self.first_period_op_ind::]:
            if op.operation_type == OperationType.BUY:
                self.end_portfolio[op.instrument_type][op.figi] += op.quantity
            elif op.operation_type == OperationType.SELL:
                self.end_portfolio[op.instrument_type][op.figi] -= op.quantity

    def get_cash_flows(self):
        for t in InstrumentType:
            for figi, quantity in self.begin_portfolio[t].items():
                self.all_cash_flows[t].append((self.request.begin_date,
                                              -self.request.quotations_begin[figi].to_float() * self.begin_portfolio[t][figi]))
        for op in self.request.operations[self.first_period_op_ind::]:
            self.all_cash_flows[op.instrument_type].append((op.date, op.payment.to_float()))
        for t in InstrumentType:
            for figi, quantity in self.end_portfolio[t].items():
                self.all_cash_flows[t].append((self.request.end_date,
                                              self.request.quotations_end[figi].to_float() * self.end_portfolio[t][figi]))





    def send_response(self):
        pass



