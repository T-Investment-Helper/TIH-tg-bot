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
