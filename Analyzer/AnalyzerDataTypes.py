import dataclasses
import datetime
import enum
from math import floor
from typing import Self
from tinkoff.invest import schemas


class Currency(enum.Enum):
    MIXED = ""
    RUB = "RUB"
    USD = "USD"


class InstrumentType(enum.Enum):
    SHARES = 0
    BONDS = 1

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

    def __div__(self, other: int | float):
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
    ticker: str
    instrument_type: InstrumentType
    instrument_name: str
    operation_type: OperationType
    quantity: int
    currency: Currency
    price: MoneyValue
    payment: MoneyValue


