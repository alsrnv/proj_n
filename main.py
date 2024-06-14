
import logging
import os
from dotenv import load_dotenv
from telegram_bot import TelegramBot

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
KEYCLOAK_SERVER_URL = os.getenv('KEYCLOAK_SERVER_URL')
KEYCLOAK_CLIENT_ID = os.getenv('KEYCLOAK_CLIENT_ID')
KEYCLOAK_CLIENT_SECRET = os.getenv('KEYCLOAK_CLIENT_SECRET')
DATABASE_URL = os.getenv('DATABASE_URL')

def main():

    # Load environment variables
    


    # Setup Telegram bot
    telegram_config = {
        'token': TELEGRAM_TOKEN,
        'admin_user_ids': [106876290],
        'allowed_user_ids': [106876290]
    }

    # Create OpenAI Helper and Telegram bot
    telegram_bot = TelegramBot(config=telegram_config)

    # Start the bot
    telegram_bot.run()

    return 0

if __name__ == '__main__':
    main()