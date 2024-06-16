import matplotlib.pyplot as plt
import tempfile
import pandas as pd
from sqlalchemy import create_engine

def connect_to_db():
    """
    Function to connect to the database.
    :return: engine: Database connection object.
    """
    db_config = {
        'user': 'user_main',
        'password': 'user108',
        'host': '85.193.90.86',
        'port': '5532',
        'database': 'hack_db'
    }
    connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    return create_engine(connection_string)

def get_unique_products():
    """
    Function to get a list of unique products.
    :return: List of unique products.
    """
    engine = connect_to_db()
    query = 'SELECT DISTINCT "Счет" FROM financial_data'
    df = pd.read_sql(query, engine)
    return df['Счет'].tolist()

def generate_inventory_for_product(product_name):
    """
    Function to generate inventory chart for a specific product.
    :param product_name: Name of the product.
    :return: Path to the saved chart image.
    """
    engine = connect_to_db()
    query = f'''
    SELECT "Дата", "Остаток"
    FROM inventory_data
    WHERE "Товар" = '{product_name}'
    ORDER BY "Дата"
    '''
    df = pd.read_sql(query, engine)

    if df.empty:
        raise ValueError(f"No data found for product: {product_name}")

    fig, ax = plt.subplots()
    ax.plot(df['Дата'], df['Остаток'], marker='o', linestyle='-')
    ax.set_title(f'История остатков для {product_name}')
    ax.set_xlabel('Дата')
    ax.set_ylabel('Остаток')

    # Save the chart to a temporary file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        plt.savefig(tmp_file.name)
        tmp_file_path = tmp_file.name

    return tmp_file_path

def generate_inventory_chart(data):
    """
    Generates a bar chart for inventory data.
    
    Parameters:
        data (dict): Dictionary with 'Товар' and 'Количество' keys.
    
    Returns:
        str: Path to the saved chart image.
    """
    fig, ax = plt.subplots()
    ax.bar(data['Товар'], data['Количество'])
    ax.set_title('Складские остатки')
    ax.set_xlabel('Товар')
    ax.set_ylabel('Количество')

    # Save the chart to a temporary file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        plt.savefig(tmp_file.name)
        tmp_file_path = tmp_file.name

    return tmp_file_path

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

    # Save the chart to a temporary file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        plt.savefig(tmp_file.name)
        tmp_file_path = tmp_file.name

    return tmp_file_path
