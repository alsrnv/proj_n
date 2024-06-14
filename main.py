import logging
import os
from dotenv import load_dotenv
from telegram_bot import TelegramBot

# Load environment variables from .env file
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
KEYCLOAK_SERVER_URL = os.getenv('KEYCLOAK_SERVER_URL')
KEYCLOAK_CLIENT_ID = os.getenv('KEYCLOAK_CLIENT_ID')
KEYCLOAK_CLIENT_SECRET = os.getenv('KEYCLOAK_CLIENT_SECRET')
DATABASE_URL = os.getenv('DATABASE_URL')

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Ensure environment variables are loaded
    if not all([TELEGRAM_TOKEN, KEYCLOAK_SERVER_URL, KEYCLOAK_CLIENT_ID, KEYCLOAK_CLIENT_SECRET, DATABASE_URL]):
        logger.error("One or more environment variables are missing!")
        return 1

    # Setup Telegram bot
    telegram_config = {
        'token': TELEGRAM_TOKEN,
        'admin_user_ids': ["106876290"],
        'allowed_user_ids': ["106876290"]
    }

    # Create Telegram bot instance
    telegram_bot = TelegramBot(config=telegram_config)

    # Start the bot
    telegram_bot.run()

    return 0

if __name__ == '__main__':
    main()
