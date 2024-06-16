import matplotlib.pyplot as plt
import tempfile
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def day_of_quarter(quarter, day_type, year='2022'):
    """
    Функция для определения первого или последнего дня квартала.
    :param quarter:
    :param day_type:
    :param year:
    :return:
    """
    quarter = int(quarter)
    year = int(year)

    if day_type == 'first':
        # Определяем первый месяц квартала
        first_month_of_quarter = (quarter - 1) * 3 + 1
        # Определяем первый день квартала
        first_day = datetime(year, first_month_of_quarter, 1)
        return first_day.strftime('%d-%m-%Y')

    elif day_type == 'last':
        # Определяем последний месяц квартала
        last_month_of_quarter = quarter * 3
        if last_month_of_quarter == 12:
            last_day = datetime(year, last_month_of_quarter, 31)
        else:
            # Определяем первый день следующего месяца
            first_day_of_next_month = datetime(year, last_month_of_quarter % 12 + 1, 1)
            # Вычитаем один день, чтобы получить последний день текущего месяца
            last_day = first_day_of_next_month - timedelta(days=1)
        return last_day.strftime('%d-%m-%Y')


def history_remains_for_product(product_name, engine):
    """
    Функция для получения истории остатков товара.
    :param product_name: Название товара.
    :return: values: Словарь с датами и остатками товара.
    """
    # Создаем подключение к базе данных

    values = {}
    for num_quater in range(1, 5):
        query = f'''select "Счет", "Сальдо на начало периода (Кол-во Де", "Сальдо на конец периода (Кол-во Деб", "Квартал"
                    from financial_data
                    where "Код" is not NULL
                    and "Счет" = '{product_name}'
                    and "Квартал" = '{num_quater}'
                '''
        num_at_beginning = pd.read_sql(query, engine).fillna(0)['Сальдо на начало периода (Кол-во Де']
        if len(num_at_beginning) == 0:
            values[day_of_quarter(num_quater, 'first')] = 0
        else:
            values[day_of_quarter(num_quater, 'first')] = int(num_at_beginning.sum())
        if num_quater == 4:
            num_at_end = pd.read_sql(query, engine).fillna(0)['Сальдо на конец периода (Кол-во Деб']
            if len(num_at_end) == 0:
                values[day_of_quarter(num_quater, 'last')] = 0
            else:
                values[day_of_quarter(num_quater, 'last')] = int(num_at_end.sum())

    return values


def generate_inventory_chart(data, product_name):
    """
    Generates a bar chart for inventory data.
    
    Parameters:
        data (dict): Dictionary with 'Товар' and 'Количество' keys.
        product_name(str): Name of the product.
    Returns:
        str: Path to the saved chart image.
    """

    colors = ['red', 'orange', 'yellow', 'green']

    # Определение цвета для каждого значения в данных
    color_scale = [colors[int(value / max(data.values()) * (len(colors) - 1))] for value in data.values()]

    fig = make_subplots(rows=1, cols=len(data), shared_yaxes=True,
                        subplot_titles=list(data.keys()))

    # Добавляем каждый график в соответствующий подграфик с указанием цвета
    for i, (date, value) in enumerate(data.items(), start=1):
        fig.add_trace(go.Bar(x=[date], y=[value], name=date, showlegend=False, marker=dict(color=color_scale[i - 1])),
                      row=1, col=i)

    # Обновляем макет для лучшей читаемости и добавляем подпись оси Y только к первому подграфику
    fig.update_yaxes(title_text="Количество", row=1, col=1)
    fig.update_xaxes(showticklabels=False)  # Убираем подписи на оси X

    # Обновляем общие параметры макета
    fig.update_layout(
        height=400,
        width=800,
        title_text=f"Остаток {product_name}",
        title_x=0.5  # Центрируем заголовок
    )
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        fig.write_image(tmp_file.name)
    tmp_file_path = tmp_file.name

    return tmp_file_path


def all_distinct_products(engine):
    """
    Функция для получения списка всех уникальных товаров.
    :return: Список уникальных товаров.
    """
    query = f'''select distinct "Счет" from financial_data'''
    return pd.read_sql(query, engine)['Счет'].to_list()


def return_best_match(product_name, lst_titles):
    """
    Функция для нахождения наиболее похожего названия товара.
    Args:
        product_name: исходное название товара.
        lst_titles: список названий товаров для сравнения.

    Returns: best_match: Наиболее похожее название товара.

    """
    # Преобразование текста в TF-IDF векторы
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(lst_titles + [product_name])

    # Вычисление косинусного сходства
    cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])

    # Нахождение наиболее похожего названия
    best_match_index = cosine_sim.argmax()
    best_match = lst_titles[best_match_index]
    return best_match


def make_kpgz_spgz_ste(product_name, engine):
    query = f"""SELECT distinct("Название СТЕ")
    FROM reference_data
    """
    # Список названий и текстовое название для сравнения
    titles_in_reference_data = pd.read_sql(query, engine)["Название СТЕ"].tolist()
    reference_data_title = return_best_match(product_name, titles_in_reference_data)
    query = f"""SELECT *
    FROM reference_data
    WHERE "Название СТЕ" = '{reference_data_title}'
    LIMIT 1
    """
    # return pd.read_csv('kpgz_spgz_ste.csv').iloc[0].to_dict()

    return pd.read_sql(query, engine).iloc[0].to_dict()


def make_contracts(product_name, engine):
    query = f"""SELECT distinct("Наименование СПГЗ")
        FROM contracts
        """
    # Список названий и текстовое название для сравнения
    titles_in_contracts = pd.read_sql(query, engine)["Наименование СПГЗ"].tolist()
    contracts_title = return_best_match(product_name, titles_in_contracts)
    query = f"""SELECT *
            FROM contracts
            where "Наименование СПГЗ" = '{contracts_title}'
            limit 1
            """
    # return pd.read_csv('kpgz_spgz_ste.csv').iloc[0].to_dict()

    return pd.read_sql(query, engine).iloc[0].to_dict()


def make_financial_data(product_name, engine):
    query = f"""SELECT *
            FROM financial_data
            where "Счет" = '{product_name}'
            limit 1
            """
    return pd.read_sql(query, engine).iloc[0].to_dict()


def make_one_row(product_name, cnt_to_buy, sum_to_buy, engine):
    product_kpgz_spgz_ste = make_kpgz_spgz_ste(product_name, engine)
    product_contracts = make_contracts(product_name, engine)
    product_financial = make_financial_data(product_name, engine)

    one_row = {}
    one_row["DeliverySchedule"] = {  # График поставки
        "dates": {
            "end_date": day_of_quarter(1, 'last', str(product_financial['Год'] + 1)),
            # Дата окончания поставки – данные рождаются в процессе прогнозирования
            "start_date": day_of_quarter(1, 'first', str(product_financial['Год'] + 1))
            # Дата начала поставки– данные рождаются в процессе прогнозирования
        },
        "deliveryAmount": cnt_to_buy,  # Объем поставки– данные рождаются в процессе прогнозирования
        "deliveryConditions": "",  # Условия поставки– данные рождаются в процессе прогнозирования
        "year": product_financial['Год'] + 1  # Год– данные рождаются в процессе прогнозирования
    }
    one_row["address"] = {  # Адрес поставки– данные рождаются в процессе прогнозирования
        "gar_id": "",  # Идентификатор ГАР – это федеральный справочник адресов
        "text": ""  # Адрес в текстовой форме – если не нашли ГАР – можно использовать это полне
    }

    one_row['entityId'] = product_kpgz_spgz_ste['СПГЗ']
    one_row['id'] = product_kpgz_spgz_ste['СПГЗ код']
    one_row['nmc'] = sum_to_buy  # сумма
    one_row['okei_code'] = ''
    one_row['purchaseAmount'] = cnt_to_buy  # Объем поставки - от дениса

    one_row['spgzCharacteristics'] = []
    one_row['spgzCharacteristics'].append(
        {"characteristicName": product_contracts['Наименование СПГЗ'],  # характеристика
         "characteristicSpgzEnums": [
         ]})

    one_row['spgzCharacteristics'][0]['characteristicSpgzEnums'].append({
        "value": product_contracts['ID СПГЗ']
    })
    one_row['spgzCharacteristics'][0]['conditionTypeId'] = 0  # тип условия
    one_row['spgzCharacteristics'][0]['kpgzCharacteristicId'] = product_contracts[
        'Конечный код КПГЗ']  # идентификатор характерис��ики КПГЗ
    one_row['spgzCharacteristics'][0]['okei_id'] = 0  # идентификатор ОКЕИ
    one_row['spgzCharacteristics'][0]['selectType'] = 0  # тип выбора
    one_row['spgzCharacteristics'][0]['typeId'] = 0  # тип
    one_row['spgzCharacteristics'][0]['value1'] = 0  # значение 1
    one_row['spgzCharacteristics'][0]['value2'] = 0  # значение 2
    return one_row


def exponential_smoothing(series, alpha):
    '''
    Функция для применения экспоненциального сглаживания к временному ряду.
    Args:
        series:
        alpha:

    Returns:

    '''
    result = [series[0]]

    for n in range(1, len(series)):
        result.append(alpha * series[n] + (1 - alpha) * result[n - 1])
    return result[-1]


def get_cnt_sum(product_name: str, engine):
    try:
        query = f"""select * from financial_data where "Счет" = '{product_name}' and "Обороты за период (Сумма Дебет)" is not NULL"""  # and "Сальдо на начало периода (Сумма Дебет)" is not NULL
        data = pd.read_sql(query, engine)
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

        cnt_to_buy = exponential_smoothing(np.asarray(list(bought_cnt.values())), 0.6)
        sum_to_buy = exponential_smoothing(np.asarray(list(bought_sum.values())), 0.6)

        return int(np.ceil(cnt_to_buy)), int(np.ceil(sum_to_buy))
    except Exception as e:
        print(e)
        return -1, -1


def all_regular_product_names(engine):
    query = f'''select "Счет", "Обороты за период (Кол-во Дебет)", "Обороты за период (Кол-во Кредит)", "Квартал"
                        from financial_data
                        where "Код" is not NULL '''
    financial_data_df = pd.read_sql(query, engine)
    lst = financial_data_df['Счет'].unique().tolist()
    lst_regular = []
    for product_name in lst:
        df = financial_data_df[financial_data_df['Счет'] == product_name]
        if (df.groupby('Квартал')['Обороты за период (Кол-во Дебет)'].sum() > 0).sum() >= 2:
            lst_regular.append(product_name)
    return lst_regular


def generate_stats_chart(stats_data):
    """
    Generates a line chart for stats data.
    
    Parameters:
        stats_data (dict): Dictionary with 'Дата' and 'Значение' keys.
    
    Returns:
        str: Path to the saved chart image.
    """
    fig, ax = plt.subplots()
    ax.plot(stats_data['Дата'], stats_data['Значение'])
    ax.set_title('Статистика использования')
    ax.set_xlabel('Дата')
    ax.set_ylabel('Значение')

    # Сохранение графика во временный файл
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        plt.savefig(tmp_file.name)
        tmp_file_path = tmp_file.name

    return tmp_file_path
