# from flask import Flask, request, jsonify, send_from_directory
# from keycloak import KeycloakOpenID
# import os
# import logging
# import requests

# logging.basicConfig(level=logging.DEBUG)

# class WebApp:
#     def __init__(self):
#         self.app = Flask(__name__)
#         self.app.secret_key = os.getenv('FLASK_SECRET_KEY')

#         self.KEYCLOAK_SERVER_URL = os.getenv('KEYCLOAK_SERVER_URL')
#         self.KEYCLOAK_REALM_NAME = os.getenv('KEYCLOAK_REALM_NAME')
#         self.KEYCLOAK_CLIENT_ID = os.getenv('KEYCLOAK_CLIENT_ID')
#         self.KEYCLOAK_CLIENT_SECRET = os.getenv('KEYCLOAK_CLIENT_SECRET')
#         self.REDIRECT_URI = os.getenv('REDIRECT_URI')
#         self.telegram_bot_url = os.getenv('TELEGRAM_BOT_URL')

#         self.add_routes()

#     def add_routes(self):
#         self.app.add_url_rule('/login.html', 'serve_login_page', self.serve_login_page)
#         self.app.add_url_rule('/login', 'login', self.login, methods=['POST'])
#         self.app.add_url_rule('/select_product', 'select_product', self.select_product, methods=['POST'])

#     def serve_login_page(self):
#         logging.debug("Serving login.html")
#         return send_from_directory('templates', 'login.html')

#     def login(self):
#         logging.debug("Login endpoint hit")
#         data = request.json
#         logging.debug(f"Received data: {data}")
#         username = data.get('username')
#         password = data.get('password')
#         user_id = data.get('user_id')

#         keycloak_openid = KeycloakOpenID(
#             server_url=self.KEYCLOAK_SERVER_URL,
#             client_id=self.KEYCLOAK_CLIENT_ID,
#             realm_name=self.KEYCLOAK_REALM_NAME,
#             client_secret_key=self.KEYCLOAK_CLIENT_SECRET,
#             verify=False  # Отключение проверки SSL
#         )
#         try:
#             token = keycloak_openid.token(
#                 username=username,
#                 password=password,
#                 grant_type='password'
#             )
#             logging.debug(f"Token received: {token}")
#             response = requests.post(f"{self.telegram_bot_url}/login_result", json={'user_id': user_id, 'success': True})
#             return jsonify(token), 200
#         except Exception as e:
#             logging.error(f"Failed to get Keycloak token: {str(e)}")
#             response = requests.post(f"{self.telegram_bot_url}/login_result", json={'user_id': user_id, 'success': False, 'error': str(e)})
#             return jsonify({"error": str(e)}), 400

#     def select_product(self):
#         data = request.json
#         product = data.get('product')
#         user_id = data.get('user_id')

#         logging.debug(f"Product selected: {product} by user {user_id}")
#         try:
#             response = requests.post(f"{self.telegram_bot_url}/product_selected", json={'user_id': user_id, 'product': product})
#             return jsonify({"success": True}), 200
#         except Exception as e:
#             logging.error(f"Failed to process product selection: {str(e)}")
#             return jsonify({"success": False, "error": str(e)}), 400

#     def run(self):
#         logging.debug("Starting Flask server.")
#         try:
#             self.app.run(host='0.0.0.0', port=5000)
#         except Exception as e:
#             logging.error(f"Failed to start Flask server: {str(e)}")
