import pandas as pd
from sqlalchemy import create_engine
from IPython.display import display
import numpy as np
# import sys

import psycopg2

def double_exponential_smoothing(series, alpha, beta, horizon = 1):
    h = horizon - 1
    result = [series[0]]
    for n in range(1, len(series) + h):
        if n == 1:
            level, trend = series[0], series[1] - series[0]
        if n >= len(series): # прогнозируем
            value = result[-1]
        else:
            value = series[n]
        last_level, level = level, alpha*value + (1-alpha)*(level+trend)
        trend = beta*(level-last_level) + (1-beta)*trend
        result.append(level+trend)
    return result[-horizon:]

def get_cnt_sum(product: str, period: int = 1):
    try:
        db_config = {
            'user': 'user1',
            'password': 'password1',
            'host': '85.193.90.86',
            'port': '5532',
            'database': 'hack_db'
        }
        connection_string = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"

        conn = create_engine(connection_string)
        query = f"""select * from financial_data where "Счет" = '{product}' and "Обороты за период (Сумма Дебет)" is not NULL"""
        data = pd.read_sql(query, conn)
        data = data[data['Код'].isnull() != True]
        data = data.fillna(0)

        if len(data) <= 1:
            return -2, -2

        data['used_cnt'] = data['Обороты за период (Кол-во Дебет)']
        data['used_sum'] = data['Обороты за период (Сумма Дебет)']

        bought_cnt = {1: 0, 2: 0, 3: 0, 4: 0}
        for ind, row in data.iterrows():
            bought_cnt[row['Квартал']] = row['used_cnt']
    #     bought_cnt

        bought_sum = {1: 0, 2: 0, 3: 0, 4: 0}
        for ind, row in data.iterrows():
            bought_sum[row['Квартал']] = row['used_sum']
    #     bought_sum
        
        history_cnt = np.asarray(list(bought_cnt.values()))
        history_sum = np.asarray(list(bought_sum.values()))
        
        cnt_to_buy= double_exponential_smoothing(history_cnt, 0.6, 0.4, period)
        sum_to_buy = double_exponential_smoothing(history_sum, 0.6, 0.4, period)

        return cnt_to_buy, sum_to_buy
    except Exception as e:
        print(e)
        return -1, -1
    
# def main():
#     args = sys.argv[1:]
#     print(get_cnt_sum(args[0], int(args[1])))

# if __name__ == '__main__':
#     main()