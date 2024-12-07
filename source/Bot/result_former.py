from source.Analyzer.AnalyzerDataTypes import SharesPortfolioIntervalAnalyzerResponse

def markdownify(money: str):
    res = ""
    for el in money:
        if el == '.' or el == '-':
            res += '\\'+ el
        else:
            res += el
    return res

async def form_result(response: SharesPortfolioIntervalAnalyzerResponse):
    r_a = markdownify(str(response.revenue_all))
    r_d = markdownify(str(response.revenue_dividends))
    r_wd = markdownify(str(response.revenue_without_dividends))
    p = markdownify(str(response.profit_all_xirr))
    s_g = response.shares_grew
    s_f = response.shares_fell
    result = f'''*Статистика по Вашим акциям за выбранный период*

*Полный доход:* {r_a}
*Дивидендный доход:* {r_d}
*Доход без учёта дивидендов:* {r_wd}
*Доходность:* {p}
'''
    result += "*Выросли:* "
    for i in range(len(s_g)):
        result += s_g[i]
        if i != len(s_g) - 1:
            result += ", "
        else:
            result += "\n"
    result += "*Упали:* "
    for i in range(len(s_f)):
        result += s_f[i]
        if i != len(s_f) - 1:
            result += ", "
    return result