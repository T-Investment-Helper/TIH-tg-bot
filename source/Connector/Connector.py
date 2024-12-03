import datetime

from tinkoff.invest import services, schemas, Client, GetOperationsByCursorRequest, OperationState, CandleInterval
from AnalyzerDataTypes import InstrumentOperation, Currency, MoneyValue, OperationType, InstrumentType


class Connector:
    def __init__(self, TOKEN: str):
        self.TOKEN: str = TOKEN
        self.figi_to_info: dict[str, tuple[str, str, str]] = {}

    def get_instrument_info(self, operation: schemas.Operation) -> tuple[str, str, str]:
        if operation.figi in self.figi_to_info:
            return self.figi_to_info[operation.figi]
        else:
            with Client(self.TOKEN) as client:
                inst = client.instruments.get_instrument_by(operation.instrument_uid).instrument
                self.figi_to_info = (inst.ticker, inst.class_code, inst.name)
                return self.figi_to_info[operation.figi]

    def convert_t_api_operation(self, operation: schemas.Operation):
        info = self.get_instrument_info(operation)
        curr = Currency[operation.currency.upper()]
        return InstrumentOperation(date=operation.date, ticker=info[0],
                                   instrument_type=InstrumentType.from_t_api_instrument_type(operation.instrument_type),
                                   instrument_name=info[1],
                                   exchange_code=info[2],
                                   operation_type=OperationType.from_t_api_operation_type(operation.operation_type),
                                   quantity=operation.quantity, currency=curr,
                                   price=MoneyValue(operation.price.units, operation.price.nano, curr),
                                   payment=MoneyValue(operation.payment.units, operation.payment.nano, curr))


