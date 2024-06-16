import pandas as pd
from sqlalchemy import create_engine
from IPython.display import display
import numpy as np
# import sys

import psycopg2

def exponential_smoothing(series, alpha):
    result = [series[0]] 
    
    for n in range(1, len(series)):
        result.append(alpha * series[n] + (1 - alpha) * result[n-1])
    return result[-1]

def get_cnt_sum(product: str):
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
        query = f"""select * from financial_data where "Счет" = '{product}' and "Обороты за период (Сумма Дебет)" is not NULL and "Сальдо на начало периода (Сумма Дебет)" is not NULL """
        data = pd.read_sql(query, conn)
        data = data[data['Код'].isnull() != True]
        data = data.fillna(0)

        if len(data) <= 2:
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

        cnt_to_buy = exponential_smoothing(np.asarray(list(bought_cnt.values())), 0.6)
        sum_to_buy = exponential_smoothing(np.asarray(list(bought_sum.values())), 0.6)

        return cnt_to_buy, sum_to_buy
    except Exception as e:
        print(e)
        return -1, -1
    
# def main():
#     args = sys.argv[1:]
#     print(get_cnt_sum(args[0]))

# if __name__ == '__main__':
#     main()