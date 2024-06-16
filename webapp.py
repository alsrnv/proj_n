from flask import Flask, request, jsonify, send_from_directory
import os
import logging
import requests
import asyncio

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

            # Отправка выбранного продукта обратно в Telegram бота
            telegram_bot_url = os.getenv('TELEGRAM_BOT_URL')
            if not telegram_bot_url:
                logging.error("TELEGRAM_BOT_URL is not set.")
                return jsonify({'success': False, 'error': 'TELEGRAM_BOT_URL is not set'}), 500

            try:
                import analytics
                image_path, graph_json = analytics.generate_inventory_for_product(product_name)
                asyncio.run(self.bot.product_selected({'user_id': user_id, 'product_name': product_name, 'image_path': image_path, 'graph_json': graph_json}))
                return jsonify({'success': True, 'graph_json': graph_json, 'values': analytics.history_remains_for_product(product_name, analytics.get_database_connection())}), 200
            except Exception as e:
                logging.error(f"Exception while notifying Telegram bot: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500

    def run(self):
        logging.debug("Starting Flask server.")
        self.app.run(host='0.0.0.0', port=5000)
