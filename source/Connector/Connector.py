import dataclasses
import datetime
import time
import orjson
import os
import pathlib


from tinkoff.invest import schemas, Client, OperationState, CandleInterval
from Analyzer.AnalyzerDataTypes import (InstrumentOperation, Currency, MoneyValue, OperationType,
                                         InstrumentType, SharesPortfolioIntervalConnectorRequest, SharesPortfolioIntervalAnalyzerRequest,
                                         AnalyzerRequest, ConnectorRequest, from_dict)

def mv_from_t_api_mv(mv: schemas.MoneyValue):
    return MoneyValue(units=mv.units, nano=mv.nano, curr=Currency[mv.currency])
def mv_from_t_api_quotation(q: schemas.Quotation):
    return MoneyValue(units=q.units,  nano=q.nano, curr=Currency.RUB)

def look_for_request():
    p = pathlib.Path.cwd()
    p = p.parent / "connector_requests"
    p.mkdir(exist_ok=True)
    while(True):
        requests = [req for req in p.iterdir()]
        if len(requests) != 0:
            for p in requests:
                name_parts = p.name.split("_")
                if (name_parts[1] == "shares"):
                    req = from_dict(SharesPortfolioIntervalConnectorRequest, orjson.loads(p.read_bytes()))
                    Connector(req.token_cypher, req, name_parts[2])
                    p.unlink()
                    break
                if (name_parts[1] == "bonds"):
                    pass
                    # TODO
                else:
                    continue
        time.sleep(0.5)


class Connector:
    def __init__(self, TOKEN: str, request: ConnectorRequest, req_name):
        self.req_name = req_name
        self.TOKEN: str = TOKEN
        self.figi_to_info: dict[str, tuple[str, str, str, str]] = dict()
        self.conn_request: ConnectorRequest = request
        self.analyzer_request: AnalyzerRequest = None
        self.data: dict = dict()

        try:
            self.get_data_for_analyzer_request()
            self.make_analyzer_request(SharesPortfolioIntervalAnalyzerRequest)
            self.send_data_to_analyzer()
        except Exception as e:
            print(e)
            self.make_error_response()

    def get_data_for_analyzer_request(self):
        if isinstance(self.conn_request, SharesPortfolioIntervalConnectorRequest):
            operations = self.get_shares_operations_for_period(Currency.RUB,
                                                               self.conn_request.begin_date,
                                                               self.conn_request.end_date)
            quotations = self.get_shares_quotations_for_period(self.conn_request.begin_date,
                                                               self.conn_request.end_date,
                                                               list(self.figi_to_info.keys()),
                                                               Currency.RUB)
            self.data["begin_date"] = self.conn_request.begin_date
            self.data["end_date"] = self.conn_request.end_date
            self.data["operations"] = operations
            self.data["quotations_begin"] = quotations[0]
            self.data["quotations_end"] = quotations[1]
            SharesPortfolioIntervalAnalyzerRequest(**self.data)

    def make_analyzer_request(self, request_type: dataclasses.dataclass):
        self.analyzer_request = request_type(**self.data)
    def make_error_response(self):
        p = pathlib.Path.cwd()
        p = p.parent / "analyzer_responses"
        p.mkdir(exist_ok=True)
        if isinstance(self.analyzer_request, SharesPortfolioIntervalAnalyzerRequest):
            p = p / ("response_shares_" + self.req_name)
            p.touch(exist_ok=True)
            p.write_bytes(b"")
        else:
            #TODO
            pass

    def send_data_to_analyzer(self):
        p = pathlib.Path.cwd()
        p = p.parent / "analyzer_requests"
        p.mkdir(exist_ok=True)
        if isinstance(self.analyzer_request, SharesPortfolioIntervalAnalyzerRequest):
            p = p / ("request_shares_" + self.req_name)
            p.touch(exist_ok=True)
            p.write_bytes(orjson.dumps(self.analyzer_request))
        else:
            pass
            #TODO

    def get_instrument_info(self, operation: schemas.Operation) -> tuple[str, str, str, str]:
        if operation.figi in self.figi_to_info:
            return self.figi_to_info[operation.figi]
        else:
            with Client(self.TOKEN) as client:
                if operation.figi == "":
                    operation.figi = "NOT FOUND"
                query_resp = client.instruments.find_instrument(query=operation.figi).instruments
                if not query_resp:
                    self.figi_to_info[operation.figi] = ("NOT FOUND", "NOT FOUND", "NOT FOUND", "NOT FOUND")
                    return self.figi_to_info[operation.figi]

                inst = query_resp[0]
                self.figi_to_info[operation.figi] = (inst.ticker, inst.class_code, inst.name, inst.uid)
                return self.figi_to_info[operation.figi]

    def convert_t_api_operation(self, operation: schemas.Operation):
        info = self.get_instrument_info(operation)
        curr = Currency[operation.currency.upper()]
        return InstrumentOperation(date=operation.date,
                                   figi=operation.figi,
                                   ticker=info[0],
                                   instrument_type=InstrumentType.from_t_api_instrument_type(operation.instrument_type),
                                   instrument_name=info[2],
                                   exchange_code=info[1],
                                   operation_type=OperationType.from_t_api_operation_type(operation.operation_type),
                                   quantity=operation.quantity, currency=curr,
                                   price=MoneyValue(operation.price.units, operation.price.nano, curr),
                                   payment=MoneyValue(operation.payment.units, operation.payment.nano, curr))


    def get_shares_operations_for_period(self, currency: Currency,
                                  begin_date: datetime.datetime,
                                  end_date: datetime.datetime,
                                  account_index: int = 0) -> list[InstrumentOperation]:
        #!!!Сейчас работает в режиме "операции в валюте currency", а не перевод операций к конкретной валюте
        with Client(self.TOKEN) as client:
            # print(client.users.get_accounts())
            # print(client.operations.get_portfolio(account_id=client.users.get_accounts().accounts[0].id))
            account_id = client.users.get_accounts().accounts[account_index].id
            operations = [self.convert_t_api_operation(op) for op in
                          client.operations.get_operations(account_id=account_id,
                                                           from_=client.users.get_accounts().accounts[account_index].opened_date,
                                                           to=end_date,
                                                           state=OperationState.OPERATION_STATE_EXECUTED).operations
                          if (op.instrument_type == "share" and
                              op.currency == currency.value.lower() and
                              op.state == schemas.OperationState.OPERATION_STATE_EXECUTED)
                          ]

            # def get_request(cursor=""):
            #     return GetOperationsByCursorRequest(
            #         from_=client.users.get_accounts().accounts[account_index].opened_date,
            #         to=end_date,
            #         account_id=account_id,
            #         cursor=cursor,
            #         state=OperationState.OPERATION_STATE_EXECUTED
            #     )
            # operations = []
            # new_operations = client.operations.get_operations_by_cursor(get_request())
            # operations.extend(new_operations.items)
            # while new_operations.has_next:
            #     request = get_request(cursor=new_operations.next_cursor)
            #     new_operations = client.operations.get_operations_by_cursor(request)
            #     operations.extend(new_operations.items)


        # for o in operations:
            # a = orjson.dumps(o)
            # assert o == from_dict(InstrumentOperation, orjson.loads(a))

        return operations


    def get_shares_quotations_for_period(self, begin_date: datetime.datetime,
                                         end_date: datetime.datetime,
                                         shares_figi: list[str],
                                         curr: Currency) -> tuple[dict[str, MoneyValue], dict[str, MoneyValue]]:
        begin_quotations: dict = {}
        end_quotations: dict = {}
        with Client(self.TOKEN) as client:
            for figi in shares_figi:
                if figi == "NOT FOUND":
                    continue
                begin_quotations[figi] = MoneyValue(0, 0, Currency.RUB)
                end_quotations[figi] = MoneyValue(0, 0, Currency.RUB)
                b_quots = [q for q in client.market_data.get_candles(
                                                                     from_=begin_date - datetime.timedelta(1), to=begin_date,
                                                                     interval=CandleInterval.CANDLE_INTERVAL_DAY,
                                                                     instrument_id=self.figi_to_info[figi][3]).candles]
                while not b_quots:
                    begin_date -= datetime.timedelta(1)
                    b_quots = [q for q in client.market_data.get_candles(
                                                              from_=begin_date - datetime.timedelta(1), to=begin_date,
                                                              interval=CandleInterval.CANDLE_INTERVAL_DAY,
                                                              instrument_id=self.figi_to_info[figi][3]).candles]

                e_quots = [q for q in client.market_data.get_candles(
                                                                     from_=end_date - datetime.timedelta(1), to=end_date,
                                                                     interval=CandleInterval.CANDLE_INTERVAL_DAY,
                                                                     instrument_id=self.figi_to_info[figi][3]).candles]
                while not e_quots:
                    end_date -= datetime.timedelta(1)
                    e_quots = [q for q in client.market_data.get_candles(
                                                              from_=end_date - datetime.timedelta(1), to=end_date,
                                                              interval=CandleInterval.CANDLE_INTERVAL_DAY,
                                                              instrument_id=self.figi_to_info[figi][3]).candles]
                if len(b_quots) != 0:
                    for q in b_quots:
                        begin_quotations[figi] = begin_quotations[figi] + (
                                    mv_from_t_api_quotation(q.low) + mv_from_t_api_quotation(q.high)) / 2
                    begin_quotations[figi] /= len(b_quots)
                else:
                    raise ValueError

                if len(e_quots) != 0:
                    for q in e_quots:
                        end_quotations[figi] = end_quotations[figi] + (mv_from_t_api_quotation(q.low) + mv_from_t_api_quotation(q.high)) / 2
                    end_quotations[figi] /= len(e_quots)
                else:
                    raise ValueError
        return (begin_quotations, end_quotations)



if __name__ == "__main__":
    look_for_request()
