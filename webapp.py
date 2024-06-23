from flask import Flask, request, jsonify, send_from_directory
import os
import logging
import requests
import asyncio
import json

class WebApp:
    def __init__(self, bot):
        self.app = Flask(__name__)
        self.app.secret_key = os.getenv('FLASK_SECRET_KEY')
        self.bot = bot  # Сохраняем объект bot в атрибуте класса
        self.setup_routes()
        self.latest_json = None  # Сохраняем последний JSON для редактирования

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

        @self.app.route('/get_regular_products')
        def get_regular_products():
            logging.debug("Serving regular product list")
            import analytics
            engine = analytics.get_database_connection()
            products = analytics.all_regular_product_names(engine)
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
            
        @self.app.route('/make_prediction.html')
        def serve_make_prediction_page():
            logging.debug("Serving make_prediction.html")
            return send_from_directory('templates', 'make_prediction.html')

        @self.app.route('/product_prediction', methods=['POST'])
        def product_prediction():
            data = request.json
            logging.debug(f"Received prediction request: {data}")
            product_name = data.get('product_name')
            period = data.get('period')
            user_id = data.get('user_id')

            if not product_name or not period or not user_id:
                logging.error("Missing user_id, product_name, or period")
                return jsonify({'success': False, 'error': 'Missing user_id, product_name, or period'}), 400

            try:
                import analytics
                image_path, graph_json = analytics.get_cnt_sum(product_name, analytics.get_database_connection(), period=int(period), picture=True)
                asyncio.run(self.bot.product_prediction_selected({'user_id': user_id, 'product_name': product_name, 'image_path': image_path, 'graph_json': graph_json}))
                return jsonify({'success': True, 'graph_json': graph_json, 'values': analytics.get_cnt_sum(product_name, analytics.get_database_connection(), period=int(period), picture=False)}), 200
            except Exception as e:
                logging.error(f"Exception while notifying Telegram bot: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/edit_json.html')
        def serve_edit_json_page():
            logging.debug("Serving edit_json.html")
            return send_from_directory('templates', 'edit_json.html')

        @self.app.route('/get_json', methods=['GET'])
        def get_json():
            logging.debug("Serving JSON for editing")
            try:
                with open('final_answer.json', 'r', encoding='utf-8') as json_file:
                    json_data = json.load(json_file)
                return jsonify(json_data)
            except Exception as e:
                logging.error(f"Failed to load JSON: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/update_json', methods=['POST'])
        def update_json():
            data = request.json
            logging.debug(f"Received JSON update: {data}")
            try:
                with open('final_answer.json', 'w', encoding='utf-8') as json_file:
                    json.dump(data, json_file, ensure_ascii=False, indent=4)
                
                asyncio.run(self.bot.send_json_file(chat_id=data['CustomerId'], context=self.bot.application))
                return jsonify({'success': True}), 200
            except Exception as e:
                logging.error(f"Failed to update JSON: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500

    def run(self):
        logging.debug("Starting Flask server.")
        self.app.run(host='0.0.0.0', port=5000)
