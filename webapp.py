from flask import Flask, request, jsonify, send_from_directory
import os
import logging
import requests
import asyncio
import pandas as pd
import plotly.express as px
import io
from telegram import Bot

class WebApp:
    def __init__(self, bot):
        self.app = Flask(__name__)
        self.app.secret_key = os.getenv('FLASK_SECRET_KEY')
        self.bot = bot  # Сохраняем объект bot в атрибуте класса
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/login.html')
        def serve_login_page():
            logging.debug("Serving login.html")
            return send_from_directory('templates', 'login.html')

        @self.app.route('/products.html')
        def serve_products_page():
            logging.debug("Serving products.html")
            return send_from_directory('templates', 'products.html')

        @self.app.route('/get_products')
        def get_products():
            logging.debug("Serving product list")
            import analytics
            products = analytics.get_unique_products()
            return jsonify({'products': products})

        @self.app.route('/product_selection', methods=['POST'])
        def product_selection():
            data = request.json
            logging.debug(f"Received product selection: {data}")
            product_name = data.get('product_name')
            user_id = data.get('user_id')

            if not product_name or not user_id:
                logging.error("Missing user_id or product_name")
                return jsonify({'success': False, 'error': 'Missing user_id or product_name'}), 400

            import analytics
            engine = analytics.get_database_connection()
            product_data = analytics.history_remains_for_product(product_name, engine)

            if not product_data:
                return jsonify({'error': 'Нет данных для продукта'}), 400

            fig = px.line(x=list(product_data.keys()), y=list(product_data.values()), title=f'Остатки для продукта {product_name}')
            fig.update_layout(
                xaxis_title='Дата',
                yaxis_title='Остаток',
                template='plotly_white'
            )

            # Сохранение графика как изображение для отправки в Telegram
            img_bytes = io.BytesIO()
            fig.write_image(img_bytes, format='png')
            img_bytes.seek(0)

            # Отправка изображения графика в Telegram
            bot = Bot(token=os.getenv('TELEGRAM_TOKEN'))
            bot.send_photo(chat_id=user_id, photo=img_bytes)

            # Возврат данных для отображения интерактивного графика
            graph_json = fig.to_json()
            return jsonify({'graph_json': graph_json, 'success': True})

    def run(self):
        logging.debug("Starting Flask server.")
        self.app.run(host='0.0.0.0', port=5000)
