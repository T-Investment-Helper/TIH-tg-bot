import dataclasses
import datetime
import enum
import typing
from math import floor
from typing import Self

from tinkoff.invest import schemas

#ВАЖНО!!! from_dict парсит ТОЛЬКО датаклассы со следующими ограничениями:

#Поля должны быть dict, int, str, EnumType, tuple[str] или другой dataclass/tuple[dataclass]/dict[str, dataclass] такого же вида.

def from_dict(cls: dataclasses.dataclass, d: dict) -> dataclasses.dataclass:
    new_d = dict()
    val = None
    for f in dataclasses.fields(cls):
        if isinstance(d[f.name], int):
            val = d[f.name]
        elif isinstance(d[f.name], float):
            val = d[f.name]

        elif isinstance(d[f.name], str):
            str_val = d[f.name]
            if f.type == int:
                val = int(str_val)
            elif f.type == str:
                val = str_val
            elif f.type == datetime.datetime:
                val = datetime.datetime.fromisoformat(str_val)
            elif isinstance(f.type, enum.EnumType):
                val = f.type[str_val]
            elif "from_str" in dir(f.type):
                val = f.type.from_str(str_val)
        elif isinstance(d[f.name], dict):
            dict_val = d[f.name]
            if typing.get_origin(f.type) == dict:
                new_dict_val = dict()
                for key, value in dict_val.items():
                    new_dict_val[key] = from_dict(typing.get_args(f.type)[1], value)
                val = new_dict_val
            elif "from_dict" in dir(f.type):
                val = f.type.from_dict(dict_val)
            else:
                val = from_dict(f.type, dict_val)
        elif isinstance(d[f.name], list):
            tuple_val = d[f.name][:]
            if typing.get_args(f.type)[0] == str:
                val = tuple(tuple_val)
            else:
                for i in range(len(tuple_val)):
                    tuple_val[i] = from_dict(typing.get_args(f.type)[0], d[f.name][i])
                val = tuple(tuple_val)

        new_d[f.name] = val
    return cls(**new_d)


# @dataclasses


class Currency(enum.Enum):
    NONE = "NONE"
    MIXED = "MXD"
    RUB = "RUB"
    USD = "USD"


class InstrumentType(enum.Enum):
    SHARES = "SHARES"
    BONDS = "BONDS"
    NONE = "NONE"

    '''стоит вынести перевод типов анализатора и апи в код коннектора'''
    @classmethod
    def from_t_api_instrument_type(cls, op: str):
        if op == "share":
            return cls.SHARES
        if op == "bond":
            return cls.BONDS


class OperationType(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    DIVIDENDS = "DIVIDENDS"
    COMMISSION = "COMMISSION"
    NOTFOUND = "NOTFOUND"


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
        if op == schemas.OperationType.OPERATION_TYPE_BUY_CARD:
            return cls.BUY
        return cls.NOTFOUND



@dataclasses.dataclass
class MoneyValue:
    units: int
    nano: int
    curr: Currency

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
        nano = round((other - floor(other)) * (10 ** 9))
        return MoneyValue(units, nano, curr)

    @staticmethod
    def from_dict(d: dict):
        units = int(d["units"])
        nano = int(d["nano"])
        curr = Currency[d["curr"]]
        return MoneyValue(units, nano, curr)




    def to_float(self) -> float:
        return self.units + self.nano / (10 ** 9)


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
            return MoneyValue(val // (10 ** 18), (val // (10 ** 9)) % (10 ** 9), self.curr)
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
class BondInfo:
    ticker: str
    coupons: dict[str, MoneyValue]
    price: MoneyValue
    nominal_value: MoneyValue
    is_floating: int
    aci_value: MoneyValue
    maturity_date: datetime.datetime



@dataclasses.dataclass
class ConnectorRequest:
    pass

@dataclasses.dataclass
class SharesPortfolioIntervalConnectorRequest(ConnectorRequest):
    begin_date: datetime.datetime
    end_date: datetime.datetime
    token: str
    #account_ind: int - если реализовывать переключение между разными портфелями одного пользователя

@dataclasses.dataclass
class SingleShareIntervalConnectorRequest(ConnectorRequest):
    begin_date: datetime.datetime
    end_date: datetime.datetime
    ticker: str
    token: str



@dataclasses.dataclass
class BondPortfolioProfitConnectorRequest(ConnectorRequest):
    ticker: str
    token: str

@dataclasses.dataclass
class SingleBondExpectedProfitConnectorRequest(ConnectorRequest):
    ticker: str
    token: str

@dataclasses.dataclass
class TokenValidationConnectorRequest(ConnectorRequest):
    token: str




@dataclasses.dataclass
class AnalyzerResponse:
    pass

@dataclasses.dataclass
class SharesPortfolioIntervalAnalyzerResponse(AnalyzerResponse):
    revenue_all: MoneyValue
    revenue_dividends: MoneyValue
    revenue_without_dividends: MoneyValue
    profit_all_xirr: float
    shares_grew: list[str] #только те, который были и в НАЧАЛЕ, и в КОНЦЕ!
    shares_fell: list[str] #только те, который были и в НАЧАЛЕ, и в КОНЦЕ!

@dataclasses.dataclass
class SingleBondExpectedProfitAnalyzerResponse(AnalyzerResponse):
    profit: MoneyValue
    maturity_date: datetime.datetime

@dataclasses.dataclass
class BondPortfolioProfitAnalyzerResponse(AnalyzerResponse):
    profit: MoneyValue
    revenue: MoneyValue
    maturity_date: datetime.datetime

@dataclasses.dataclass
class SingleShareAnalyzerResponse(AnalyzerResponse):
    pass


@dataclasses.dataclass
class TokenValidationAnalyzerResponse(AnalyzerResponse):
    result: str


@dataclasses.dataclass
class AnalyzerRequest:
    pass


@dataclasses.dataclass
class SharesPortfolioIntervalAnalyzerRequest(AnalyzerRequest):
    begin_date: datetime.datetime
    end_date: datetime.datetime
    operations: tuple[InstrumentOperation, ...]
    # котировки акций - только для начального и конечного момента
    quotations_begin: dict[str, MoneyValue]
    quotations_end: dict[str, MoneyValue]

    # котировки валют - на момент ВСЕХ операций (для возможного перевода валют)
    # currency_quotations: dict[str, list[MoneyValue]]


@dataclasses.dataclass
class SingleShareAnalyzerRequest(AnalyzerRequest):
    uid: str
    figi: str
    begin_date: datetime.datetime
    end_date: datetime.datetime
    operations: tuple[InstrumentOperation, ...]
    quotations: dict[datetime.datetime, MoneyValue]
    quotation_begin: tuple[datetime.datetime, MoneyValue]
    quotation_end: tuple[datetime.datetime, MoneyValue]


@dataclasses.dataclass
class BondPortfolioProfitAnalyzerRequest(AnalyzerRequest):
    ticker: str
    operations: tuple[InstrumentOperation, ...]


@dataclasses.dataclass
class SingleBondExpectedProfitAnalyzerRequest(AnalyzerRequest):
    ticker: str
    bond_info: BondInfo


class ConnectorExceptions(enum.Enum):
    InvalidToken: Exception



# @dataclasses.dataclass
# class SingleShareIntervalRequest(AnalyzerRequest):
#     begin_date: datetime.datetime
#     end_date: datetime.datetime
#     operations: list[OperationType]
#     # котировки акций - только для начального и конечного момента
#     shares_quotations: (dict[str, MoneyValue], dict[str, MoneyValue])
#     # котировки валют - на момент ВСЕХ операций (для возможного перевода валют)
#     currency_quotations: dict[str, list[MoneyValue]]
