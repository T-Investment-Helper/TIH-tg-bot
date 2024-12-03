import datetime
import orjson

from tinkoff.invest import services, schemas, Client, GetOperationsByCursorRequest, OperationState, CandleInterval
from AnalyzerDataTypes import (InstrumentOperation, Currency, MoneyValue, OperationType,
                               InstrumentType, SharesPortfolioIntervalConnectorRequest, SharesPortfolioIntervalAnalyzerRequest,
                               AnalyzerRequest, ConnectorRequest)

def mv_from_t_api_mv(mv: schemas.MoneyValue):
    return MoneyValue(units=mv.units, nano=mv.nano, curr=Currency[mv.currency])
def mv_from_t_api_quotation(q: schemas.Quotation):
    return MoneyValue(units=q.units,  nano=q.nano, curr=Currency.NONE)

class Connector:
    def __init__(self, TOKEN: str, request: ConnectorRequest):
        self.TOKEN: str = TOKEN
        self.figi_to_info: dict[str, tuple[str, str, str, str]] = dict()
        self.conn_request: ConnectorRequest = request
        self.analyzer_request: AnalyzerRequest
        self.data: dict = dict()

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
            self.data["quotations"] = quotations


        #else: TODO

    def send_data_to_analyzer(self):
        # serialize
        orjson.dumps(self.data)
        # send json TODO

    def get_instrument_info(self, operation: schemas.Operation) -> tuple[str, str, str, str]:
        if operation.figi in self.figi_to_info:
            return self.figi_to_info[operation.figi]
        else:
            with Client(self.TOKEN) as client:
                inst = client.instruments.find_instrument(query=operation.figi).instruments[0]
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
            account_id = client.users.get_accounts().accounts[account_index].id

            operations = [self.convert_t_api_operation(op) for op in
                          client.operations.get_operations(account_id=account_id,
                                                           from_=begin_date,
                                                           to=end_date,
                                                           state=OperationState.OPERATION_STATE_EXECUTED).operations
                          if (op.instrument_type == "share" and
                              op.currency == currency.value.lower() and
                              op.state == schemas.OperationState.OPERATION_STATE_EXECUTED)
                          ]

        return operations


    def get_shares_quotations_for_period(self, begin_date: datetime.datetime,
                                         end_date: datetime.datetime,
                                         shares_figi: list[str],
                                         curr: Currency) -> tuple[dict[str, MoneyValue], dict[str, MoneyValue]]:
        begin_quotations: dict = {}
        end_quotations: dict = {}
        with Client(self.TOKEN) as client:
            for figi in shares_figi:
                begin_quotations[figi] = MoneyValue(0, 0, Currency.NONE)
                end_quotations[figi] = MoneyValue(0, 0, Currency.NONE)
                b_quots = [q for q in client.market_data.get_candles(from_=begin_date, to=begin_date + datetime.timedelta(10),
                                                             interval=CandleInterval.CANDLE_INTERVAL_DAY,
                                                                     instrument_id=self.figi_to_info[figi][3]).candles]
                e_quots = [q for q in client.market_data.get_candles(from_=end_date, to=end_date + datetime.timedelta(10),
                                                             interval=CandleInterval.CANDLE_INTERVAL_DAY,
                                                                     instrument_id=self.figi_to_info[figi][3]).candles]
                if len(b_quots) != 0:
                    for q in b_quots:
                        begin_quotations[figi] = begin_quotations[figi] + (
                                    mv_from_t_api_quotation(q.low) + mv_from_t_api_quotation(q.high)) / 2
                    begin_quotations[figi] /= len(b_quots)

                if len(e_quots) != 0:
                    for q in e_quots:
                        end_quotations[figi] = end_quotations[figi] + (mv_from_t_api_quotation(q.low) + mv_from_t_api_quotation(q.high)) / 2
                    end_quotations[figi] /= len(b_quots)
        return (begin_quotations, end_quotations)


