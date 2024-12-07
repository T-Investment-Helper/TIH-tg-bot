import unittest

from unittest import IsolatedAsyncioTestCase

from source.Bot.result_former import form_result
from source.Analyzer.AnalyzerDataTypes import SharesPortfolioIntervalAnalyzerResponse, MoneyValue, Currency

response = SharesPortfolioIntervalAnalyzerResponse(
    revenue_all=MoneyValue.from_float(-120.3, Currency.RUB),
    revenue_dividends=MoneyValue.from_float(123.3, Currency.RUB),
    revenue_without_dividends=MoneyValue.from_float(-1020.3, Currency.RUB),
    profit_all_xirr=20.5,
    shares_grew=['MTSS', 'GZP'],
    shares_fell=['YAND']
)

result = '''*Статистика по Вашим акциям за выбранный период*

*Полная прибыль:* \-120\.3 RUB
*Дивидендная прибыль:* 123\.3 RUB
*Прибыль без учёта дивидендов:* \-1020\.3 RUB
*Доходность:* 20\.5
*Выросли:* MTSS, GZP
*Упали:* YAND'''

class TestResultFormer(IsolatedAsyncioTestCase):
    async def test_form_result(self):
        test_result = await form_result(response)
        self.assertEqual(test_result, result)

if __name__ == '__main__':
    unittest.main()