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
        self.all_cash_flows: dict[InstrumentType, list[tuple[datetime.datetime, float]]] = dict()
        self.instruments_cash_flow: dict[InstrumentType, dict[str, list[tuple[datetime.datetime, float]]]] = dict()
        self.operations_cash_flow: dict[OperationType, list[tuple[datetime.datetime, float]]] = dict()
        self.first_period_op_ind: int = 0

        for t in InstrumentType:
            self.begin_portfolio[t] = defaultdict(int)
            self.end_portfolio[t] = defaultdict(int)
            self.all_cash_flows[t] = []
            self.instruments_cash_flow[t] = defaultdict(list)
        for t in OperationType:
            self.operations_cash_flow[t] = []

        self.process_request()
        self.send_response()

    def process_request(self):
        if isinstance(self.request, SharesPortfolioIntervalAnalyzerRequest):
            self.get_begin_end_dates_portfolio()
            self.get_cash_flows()
            self.get_basic_stats()

    def get_begin_end_dates_portfolio(self):
        before_begin = True
        for ind, op in enumerate(self.request.operations):
            if before_begin:
                if op.date.replace(tzinfo=None) > self.request.begin_date:
                    before_begin = False
                    self.first_period_op_ind = ind
                    self.end_portfolio = copy.deepcopy(self.begin_portfolio)
                    break
                if op.figi == "NOT FOUND":
                    continue
                if op.operation_type == OperationType.BUY:
                    self.begin_portfolio[op.instrument_type][op.figi] += op.quantity
                else:
                    self.begin_portfolio[op.instrument_type][op.figi] -= op.quantity
        for op in self.request.operations[self.first_period_op_ind::]:
            if op.figi == "NOT FOUND":
                continue
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
            if op.figi == "NOT FOUND":
                continue
            self.all_cash_flows[op.instrument_type].append((op.date, op.payment.to_float()))
            self.operations_cash_flow[op.operation_type].append((op.date, op.payment.to_float()))
            self.instruments_cash_flow[op.instrument_type][op.figi].append((op.date, op.payment.to_float()))
        for t in InstrumentType:
            for figi, quantity in self.end_portfolio[t].items():
                self.all_cash_flows[t].append((self.request.end_date,
                                              self.request.quotations_end[figi].to_float() * self.end_portfolio[t][figi]))


    def get_basic_stats(self):
        if isinstance(self.request, SharesPortfolioIntervalAnalyzerRequest):
            self.response_data["revenue_all"] = MoneyValue.from_float(sum([d[1] for d in self.all_cash_flows[InstrumentType.SHARES]]), Currency.RUB)
            self.response_data["revenue_dividends"] = MoneyValue.from_float(sum([d[1] for d in self.operations_cash_flow[OperationType.DIVIDENDS]]), Currency.RUB)
            self.response_data["revenue_without_dividends"] = MoneyValue.from_float(self.response_data["revenue_all"].to_float() -
                                                               sum([d[1] for d in self.operations_cash_flow[OperationType.DIVIDENDS]]), Currency.RUB)
            self.response_data["profit_all_xirr"] = pyxirr.xirr(self.all_cash_flows[InstrumentType.SHARES])
            self.response_data["shares_grew"] = []
            self.response_data["shares_fell"] = []
            for figi in self.begin_portfolio[InstrumentType.SHARES].keys():
                if figi in self.end_portfolio[InstrumentType.SHARES].keys():
                    if self.request.quotations_begin[figi].to_float() >= self.request.quotations_end[figi].to_float():
                        self.response_data["shares_fell"].append(figi)
                    else:
                        self.response_data["shares_grew"].append(figi)


    def send_response(self):
        with open("analyzer_response_test", "wb") as file:
            file.write(orjson.dumps(SharesPortfolioIntervalAnalyzerResponse(**self.response_data)))


