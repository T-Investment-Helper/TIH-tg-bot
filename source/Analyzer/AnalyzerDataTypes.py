import dataclasses
import datetime
import enum
from math import floor
from typing import Self
from tinkoff.invest import schemas
import orjson

class Currency(enum.Enum):
    NONE = ""
    MIXED = ""
    RUB = "RUB"
    USD = "USD"


class InstrumentType(enum.Enum):
    SHARES = 0
    BONDS = 1

    '''стоит вынести перевод типов анализатора и апи в код коннектора'''
    @classmethod
    def from_t_api_instrument_type(cls, op: str):
        if op == "shares":
            return cls.SHARES
        if op == "bonds":
            return cls.BONDS



class OperationType(enum.Enum):
    BUY = 0
    SELL = 1
    INPUT = 2
    OUTPUT = 3
    DIVIDENDS = 4
    COMMISSION = 5

    '''стоит вынести перевод типов анализатора и апи в код коннектора'''
    @classmethod
    def from_t_api_operation_type(cls, op: schemas.OperationType):
        if op == schemas.OperationType.OPERATION_TYPE_BUY:
            return cls.BUY
        if op == schemas.OperationType.OPERATION_TYPE_SELL:
            return cls.SELL
        if op == schemas.OperationType.OPERATION_TYPE_INPUT:
            return cls.INPUT
        if op == schemas.OperationType.OPERATION_TYPE_OUTPUT:
            return cls.OUTPUT
        if op == schemas.OperationType.OPERATION_TYPE_BROKER_FEE:
            return cls.COMMISSION
        if op == schemas.OperationType.OPERATION_TYPE_DIVIDEND:
            return cls.DIVIDENDS

@dataclasses.dataclass
class MoneyValue:
    def __init__(self, units: int, nano: int, curr: Currency):
        self.units = units
        self.nano = nano
        self.curr = curr

    @staticmethod
    def from_int(other: int, curr: Currency):
        units = other
        nano = 0
        return MoneyValue(units, nano, curr)

    @staticmethod
    def from_float(other: float, curr: Currency):
        units = floor(other)
        nano = round((other - floor(other)) ** (10 ** 9))
        return MoneyValue(units, nano, curr)


    def __add__(self, other: Self | int | float):
        if isinstance(other, MoneyValue):
            return MoneyValue(self.units + other.units + (self.nano + other.nano) // (10 ** 9),
                              (self.nano + other.nano) % (10 ** 9), self.curr)
        elif isinstance(other, int):
            return self + MoneyValue.from_int(other, self.curr)
        elif isinstance(other, float):
            return self + MoneyValue.from_float(other, self.curr)
        else:
            raise TypeError

    def __mul__(self, other: Self | int | float):
        if isinstance(other, MoneyValue):
            if self.curr != other.curr:
                raise TypeError
            val = (self.units * other.units * (10**18) +
                   (self.units * other.nano + self.nano * other.units) * (10**9) +
                   self.nano * other.nano)
            return MoneyValue(val / 10 ** 9, val % 10 ** 9, self.curr)
        elif isinstance(other, int):
            return self * MoneyValue.from_int(other, self.curr)
        elif isinstance(other, float):
            return self * MoneyValue.from_float(other, self.curr)
        else:
            raise TypeError

    def __truediv__(self, other: int | float):
        if not isinstance(other, int | float):
            raise TypeError
        return self * (1 / other)

    def __str__(self):
        return str(self.units + self.nano / (10 ** 9)) + " " + self.curr.value

    def __repr__(self):
        return str(self)


@dataclasses.dataclass
class InstrumentOperation:
    date: datetime.datetime
    figi: str
    ticker: str
    instrument_type: InstrumentType
    instrument_name: str
    exchange_code: str
    operation_type: OperationType
    quantity: int
    currency: Currency
    price: MoneyValue
    payment: MoneyValue

@dataclasses.dataclass
class ConnectorRequest:
    pass


class SharesPortfolioIntervalConnectorRequest(ConnectorRequest):
    begin_date: datetime.datetime | None
    end_date: datetime.datetime | None
    #account_ind: int - если реализовывать переключение между разными портфелями одного пользователя





@dataclasses.dataclass
class AnalyzerRequest:
    pass

@dataclasses.dataclass
class AnalyzerResponse:
    pass

@dataclasses.dataclass
class SharesPortfolioIntervalAnalyzerResponse(AnalyzerResponse):
    revenue_all_fifo: MoneyValue
    revenue_all_lifo: MoneyValue
    revenue_dividends: MoneyValue
    revenue_without_dividends: MoneyValue
    profit_all_xirr: MoneyValue
    profit_without_dividends_xirr: MoneyValue
    profit_dividends_xirr: MoneyValue
    shares_grew: list[str] #только те, который были и в НАЧАЛЕ, и в КОНЦЕ!
    shares_fell: list[str] #только те, который были и в НАЧАЛЕ, и в КОНЦЕ!





@dataclasses.dataclass
class SharesPortfolioIntervalAnalyzerRequest(AnalyzerRequest):
    begin_date: datetime.datetime
    end_date: datetime.datetime
    operations: list[OperationType]
    # котировки акций - только для начального и конечного момента
    shares_quotations: (dict[str, MoneyValue], dict[str, MoneyValue])
    # котировки валют - на момент ВСЕХ операций (для возможного перевода валют)
    # currency_quotations: dict[str, list[MoneyValue]]


@dataclasses.dataclass
class SingleShareIntervalRequest(AnalyzerRequest):
    begin_date: datetime.datetime
    end_date: datetime.datetime
    operations: list[OperationType]
    # котировки акций - только для начального и конечного момента
    shares_quotations: (dict[str, MoneyValue], dict[str, MoneyValue])
    # котировки валют - на момент ВСЕХ операций (для возможного перевода валют)
    currency_quotations: dict[str, list[MoneyValue]]

