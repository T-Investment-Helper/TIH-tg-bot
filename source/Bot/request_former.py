import datetime
from source.Analyzer.AnalyzerDataTypes import SharesPortfolioIntervalConnectorRequest

async def form_request(security_type: str, start_date=None, end_date=None):
    if start_date is not None:
        if start_date > datetime.date.today():
            start_date = datetime.date.today()
    if end_date is not None:
        if end_date > datetime.date.today():
            end_date = datetime.date.today()
    if start_date is not None and end_date is not None:
        if start_date > end_date:
            start_date, end_date = end_date, start_date
    if security_type == "акции":
        request = SharesPortfolioIntervalConnectorRequest(begin_date=datetime.datetime.combine(start_date, datetime.datetime.min.time()),
                                                          end_date=datetime.datetime.combine(end_date, datetime.datetime.min.time()),
                                                          token="")
        return request