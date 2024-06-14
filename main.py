
import logging
import os

from telegram_bot import TelegramBot

def main():

    # Load environment variables
    


    # Setup Telegram bot
    telegram_config = {
        'token': '',
        'admin_user_ids': [],
        'allowed_user_ids': []
    }

    # Create OpenAI Helper and Telegram bot
    telegram_bot = TelegramBot(config=telegram_config)

    # Start the bot
    telegram_bot.run()

    return 0

if __name__ == '__main__':
    main()