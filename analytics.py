import os
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import tempfile
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

def day_of_quarter(quarter, day_type, year='2022'):
    quarter = int(quarter)
    year = int(year)

    if day_type == 'first':
        first_month_of_quarter = (quarter - 1) * 3 + 1
        first_day = datetime(year, first_month_of_quarter, 1)
        return first_day.strftime('%d-%m-%Y')

    elif day_type == 'last':
        last_month_of_quarter = quarter * 3
        if last_month_of_quarter == 12:
            last_day = datetime(year, last_month_of_quarter, 31)
        else:
            first_day_of_next_month = datetime(year, last_month_of_quarter % 12 + 1, 1)
            last_day = first_day_of_next_month - timedelta(days=1)
        return last_day.strftime('%d-%m-%Y')

def get_database_connection():
    db_url = os.getenv('DATABASE_URL')
    engine = create_engine(db_url)
    return engine

def history_remains_for_product(product_name, engine):
    values = {}
    for num_quarter in range(1, 5):
        query = f'''SELECT "Счет", "Сальдо на начало периода (Кол-во Де", "Сальдо на конец периода (Кол-во Деб", "Квартал"
                    FROM financial_data
                    WHERE "Код" IS NOT NULL
                    AND "Счет" = '{product_name}'
                    AND "Квартал" = '{num_quarter}'
                '''
        num_at_beginning = pd.read_sql(query, engine).fillna(0)['Сальдо на начало периода (Кол-во Де']
        if len(num_at_beginning) == 0:
            values[day_of_quarter(num_quarter, 'first')] = 0
        else:
            values[day_of_quarter(num_quarter, 'first')] = int(num_at_beginning.sum())
        if num_quarter == 4:
            num_at_end = pd.read_sql(query, engine).fillna(0)['Сальдо на конец периода (Кол-во Деб']
            if len(num_at_end) == 0:
                values[day_of_quarter(num_quarter, 'last')] = 0
            else:
                values[day_of_quarter(num_quarter, 'last')] = int(num_at_end.sum())

    return values

def make_kpgz_spgz_ste(product_name, engine):
    query = f"""
    SELECT *
    FROM refences_data
    WHERE "Название СТЕ" ILIKE '%%{product_name}%%'
    LIMIT 1
    """
    return pd.read_sql(query, engine).iloc[0].to_dict()

def make_contracts(product_name, engine):
    query = f"""
    SELECT *
    FROM contracts
    WHERE "Наименование СПГЗ" ILIKE '%%{product_name}%%'
    LIMIT 1
    """
    return pd.read_sql(query, engine).iloc[0].to_dict()

def all_distinct_products(engine):
    query = f"""SELECT DISTINCT "Счет" FROM financial_data"""
    return pd.read_sql(query, engine)['Счет'].to_list()

def get_unique_products():
    engine = get_database_connection()
    query = """
    SELECT DISTINCT "Основное средство"
    FROM inventory_balances
    """
    try:
        df = pd.read_sql(query, engine)
    except Exception as e:
        raise RuntimeError(f"Ошибка при выполнении SQL запроса: {str(e)}")

    return df['Основное средство'].tolist()

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

    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        fig.write_image(tmp_file.name)
    tmp_file_path = tmp_file.name

    return tmp_file_path, graph_json

def generate_inventory_for_product(product_name):
    engine = get_database_connection()

    values = history_remains_for_product(product_name, engine)
    if not values:
        raise ValueError(f"Нет данных для продукта: {product_name}")

    return generate_inventory_chart(values, product_name)
