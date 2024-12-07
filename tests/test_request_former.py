import datetime
import unittest

from unittest import IsolatedAsyncioTestCase

from source.Bot.request_former import form_request
from source.Analyzer.AnalyzerDataTypes import SharesPortfolioIntervalConnectorRequest

class TestRequestFormer(IsolatedAsyncioTestCase):
    async def test_shares_request_forming(self):
        request = await form_request("акции", datetime.date(datetime.date.today().year + 1, datetime.date.today().month, datetime.date.today().day),
                                                          datetime.date(2020, 10, 8))
        self.assertIsInstance(request, SharesPortfolioIntervalConnectorRequest)
        start_date = request.begin_date
        end_date = request.end_date
        self.assertTrue(start_date <= datetime.datetime.today())
        self.assertTrue(end_date <= datetime.datetime.today())
        self.assertTrue(start_date <= end_date)

if __name__ == '__main__':
    unittest.main()