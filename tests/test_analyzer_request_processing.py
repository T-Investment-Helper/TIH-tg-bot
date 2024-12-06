import datetime

from Analyzer.Analyzer import Analyzer
from Analyzer.AnalyzerDataTypes import *
import pytest

def operation_mock(name: str, inst_type: InstrumentType, op_type: OperationType, date: datetime.datetime, quantity: int, payment: int,
                   currency: Currency):
    return InstrumentOperation(date=date,
                               figi=name,
                               ticker="MOCK",
                               instrument_type=inst_type,
                               instrument_name=name,
                               exchange_code="MOCK",
                               operation_type=op_type,
                               quantity=quantity,
                               currency=currency,
                               price=MoneyValue(0, 0, Currency.NONE),
                               payment=MoneyValue.from_int(payment, currency))


@pytest.mark.parametrize("operations", [
    tuple([
        operation_mock("A", InstrumentType.SHARES, OperationType.BUY,
                    datetime.datetime(2023, 1, 1),
                    100, -100, Currency.RUB)
    ]),
    tuple([
        operation_mock("A", InstrumentType.SHARES, OperationType.BUY,
                    datetime.datetime(2023, 1, 1),
                    100, -100, Currency.RUB),
        operation_mock("B", InstrumentType.SHARES, OperationType.BUY,
                    datetime.datetime(2023, 6, 1),
                    1000, -1200, Currency.RUB)
    ]),
    tuple([
        operation_mock("A", InstrumentType.SHARES, OperationType.BUY,
                    datetime.datetime(2023, 1, 1),
                    100, -100, Currency.RUB),
        operation_mock("A", InstrumentType.SHARES, OperationType.SELL,
                    datetime.datetime(2024, 1, 1),
                    100, 150, Currency.RUB)
    ]),
    tuple([
        operation_mock("A", InstrumentType.SHARES, OperationType.BUY,
                    datetime.datetime(2023, 1, 1),
                    100, -100, Currency.RUB),
        operation_mock("A", InstrumentType.SHARES, OperationType.DIVIDENDS,
                    datetime.datetime(2023, 6, 1),
                    100, 30, Currency.RUB)
    ]),
    ],
    ids=["Single share buy", "Two different shares buy", "Buy-sell share in a year",
         "Single share buy + dividends"])
def test_analyzer_get_cash_flow(operations: tuple[InstrumentOperation]):
    a = Analyzer(AnalyzerRequest(operations=operations))
    a.get_cash_flows()
    for op in operations:
        assert tuple([op.date, op.payment.to_float()]) in a.all_cash_flows[op.instrument_type]


@pytest.mark.parametrize(["operations", "begin_date", "end_date"], [
    (tuple([
        operation_mock("A", InstrumentType.SHARES, OperationType.BUY,
                    datetime.datetime(2023, 1, 1),
                    100, -100, Currency.RUB)
    ]), datetime.datetime(2022, 6, 1), datetime.datetime(2023, 6, 1)),
    (tuple([
        operation_mock("A", InstrumentType.SHARES, OperationType.BUY,
                    datetime.datetime(2023, 1, 1),
                    100, -100, Currency.RUB),
        operation_mock("B", InstrumentType.SHARES, OperationType.BUY,
                    datetime.datetime(2023, 6, 1),
                    1000, -1200, Currency.RUB)
    ]), datetime.datetime(2023, 2, 1), datetime.datetime(2023, 8, 1)),
    (tuple([
        operation_mock("A", InstrumentType.SHARES, OperationType.BUY,
                    datetime.datetime(2023, 6, 1),
                    100, -100, Currency.RUB),
        operation_mock("A", InstrumentType.SHARES, OperationType.SELL,
                    datetime.datetime(2023, 7, 1),
                    100, 150, Currency.RUB)
    ]), datetime.datetime(2023, 2, 1), datetime.datetime(2023, 8, 1)),

    ],
    ids=["Single share buy, portfoio before buy and after", "One buy before interval, one in", "Buy-sell in interval"])



def test_analyzer_get_portfolio(operations: tuple[InstrumentOperation], begin_date: datetime.datetime, end_date: datetime.datetime):
    pass

@pytest.mark.parametrize(["operations", "begin_date", "end_date"], [
    (tuple([
        operation_mock("A", InstrumentType.SHARES, OperationType.BUY,
                    datetime.datetime(2023, 1, 1),
                    100, -100, Currency.RUB)
    ]), datetime.datetime(2022, 6, 1), datetime.datetime(2023, 6, 1)),
    (tuple([
        operation_mock("A", InstrumentType.SHARES, OperationType.BUY,
                    datetime.datetime(2023, 1, 1),
                    100, -100, Currency.RUB),
        operation_mock("B", InstrumentType.SHARES, OperationType.BUY,
                    datetime.datetime(2023, 6, 1),
                    1000, -1200, Currency.RUB)
    ]), datetime.datetime(2023, 2, 1), datetime.datetime(2023, 8, 1)),
    (tuple([
        operation_mock("A", InstrumentType.SHARES, OperationType.BUY,
                    datetime.datetime(2023, 6, 1),
                    100, -100, Currency.RUB),
        operation_mock("A", InstrumentType.SHARES, OperationType.SELL,
                    datetime.datetime(2023, 7, 1),
                    100, 150, Currency.RUB)
    ]), datetime.datetime(2023, 2, 1), datetime.datetime(2023, 8, 1)),

    ],
    ids=["Single share buy, portfoio before buy and after", "One buy before interval, one in", "Buy-sell in interval"])
def test_analyzer_get_share_stats(operations: tuple[InstrumentOperation], begin_date: datetime.datetime, end_date: datetime.datetime):
    pass


@pytest.mark.parametrize("operations", [
    tuple([
        operation_mock("A", InstrumentType.SHARES, OperationType.BUY,
                    datetime.datetime(2023, 1, 2),
                    100, -100, Currency.RUB)
    ]),
    tuple([
        operation_mock("A", InstrumentType.SHARES, OperationType.BUY,
                    datetime.datetime(2022, 1, 2),
                    100, -100, Currency.RUB),
        operation_mock("B", InstrumentType.SHARES, OperationType.BUY,
                    datetime.datetime(2023, 6, 1),
                    1000, -1200, Currency.RUB)
    ]),
    tuple([
        operation_mock("A", InstrumentType.SHARES, OperationType.BUY,
                    datetime.datetime(2023, 1, 2),
                    100, -100, Currency.RUB),
        operation_mock("A", InstrumentType.SHARES, OperationType.SELL,
                    datetime.datetime(2024, 1, 1),
                    100, 150, Currency.RUB)
    ]),
    tuple([
        operation_mock("A", InstrumentType.SHARES, OperationType.BUY,
                    datetime.datetime(2023, 1, 2),
                    100, -100, Currency.RUB),
        operation_mock("A", InstrumentType.SHARES, OperationType.DIVIDENDS,
                    datetime.datetime(2023, 6, 1),
                    100, 30, Currency.RUB)
    ]),
    ],
    ids=["Single share buy", "Two different shares buy", "Buy-sell share in a year",
         "Single share buy + dividends"])

def test_analyzer_get_basic_stats(operations: tuple[InstrumentOperation],
                                  begin_date: datetime.datetime = datetime.datetime(2023, 1, 1),
                                  end_date: datetime.datetime = datetime.datetime(2024, 1, 1),
                                  quotations_begin: dict[str, MoneyValue] = {"A" : MoneyValue.from_int(1, curr=Currency.RUB), "B" : MoneyValue.from_int(1, curr=Currency.RUB)},
                                  quotations_end: dict[str, MoneyValue] = {"A" : MoneyValue.from_float(1.5, curr=Currency.RUB), "B" : MoneyValue.from_int(1.5, curr=Currency.RUB)}):
    a = Analyzer(SharesPortfolioIntervalAnalyzerRequest(begin_date=begin_date, end_date=end_date, operations=operations,
                                                        quotations_begin=quotations_begin, quotations_end=quotations_end))
    print(a.response_data["shares_grew"])
    assert a.response_data["revenue_all"].to_float() > 0
    assert a.response_data["revenue_dividends"] == MoneyValue(30, 0, Currency.RUB) or a.response_data["revenue_dividends"] == MoneyValue(0, 0, Currency.RUB)
    assert a.response_data["profit_all_xirr"] < 1 and a.response_data["profit_all_xirr"] > 0 #for this data ONLY
    assert a.response_data["shares_fell"] == []


