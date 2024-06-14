import matplotlib.pyplot as plt
import tempfile
import os

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

    # Сохранение графика во временный файл
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

    # Сохранение графика во временный файл
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        plt.savefig(tmp_file.name)
        tmp_file_path = tmp_file.name

    return tmp_file_path
