import asyncio
from flask import Flask, request, jsonify, send_from_directory
from telegram_bot import TelegramBot
import os
import logging
import requests

class WebApp:
    def __init__(self, bot):
        self.app = Flask(__name__)
        self.app.secret_key = os.getenv('FLASK_SECRET_KEY')
        self.bot = bot  # Сохраняем объект bot
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

            # Вызов метода product_selected напрямую
            try:
                asyncio.run(self.bot.product_selected(data))
                return jsonify({'success': True}), 200
            except Exception as e:
                logging.error(f"Exception while notifying Telegram bot: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500

    def run(self):
        logging.debug("Starting Flask server.")
        self.app.run(host='0.0.0.0', port=5000)
