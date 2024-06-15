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
        query = f'''select "Счет", "Сальдо на начало периода (Кол-во Де", "Обороты за период (Кол-во Дебет)", "Обороты за период (Кол-во Кредит)", "Сальдо на конец периода (Кол-во Деб", "Квартал"
                    from financial_data
                    where "Код" is not NULL
                    and "Счет" = '{product_name}'
                    and "Квартал" = '{num_quater}'
                '''
        num_at_beginning = pd.read_sql(query, engine).fillna(0)['Сальдо на начало периода (Кол-во Де']
        if len(num_at_beginning) == 0:
            values[day_of_quarter(num_quater, 'first')] = 0
        else:
            values[day_of_quarter(num_quater, 'first')] = int(num_at_beginning[0])
        if num_quater == 4:
            num_at_end = pd.read_sql(query, engine).fillna(0)['Сальдо на конец периода (Кол-во Деб']
            if len(num_at_end) == 0:
                values[day_of_quarter(num_quater, 'last')] = 0
            else:
                values[day_of_quarter(num_quater, 'last')] = int(num_at_end[0])

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
