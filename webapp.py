from flask import Flask, request, jsonify, send_from_directory
import os
import logging
import requests

class WebApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = os.getenv('FLASK_SECRET_KEY')
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
            # Отправка выбранного продукта обратно в Telegram бота
            telegram_bot_url = os.getenv('TELEGRAM_BOT_URL')
            response = requests.post(f"{telegram_bot_url}/product_selected", json={'user_id': user_id, 'product_name': product_name})
            return response.content, response.status_code

    def run(self):
        logging.debug("Starting Flask server.")
        self.app.run(host='0.0.0.0', port=5000)
