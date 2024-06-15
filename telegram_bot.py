from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import os
import json
import logging
import asyncio
import traceback
import requests
import subprocess
import tempfile
from sqlalchemy import create_engine

from analytics import generate_inventory_chart, generate_stats_chart, history_remains_for_product

START_ROUTES, END_ROUTES = range(2)


class TelegramBot:
    @staticmethod
    def __connect_to_db():
        """
        Функция для подключения к базе данных.
        :return: engine: Объект подключения к базе данных.
        """
        # Создаем подключение к базе данных
        # Параметры подключения к базе данных
        db_config = {
            'user': 'user_main',
            'password': 'user108',
            'host': '85.193.90.86',
            'port': '5532',
            'database': 'hack_db'
        }

        # Создание строки подключения
        connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"

        return create_engine(connection_string)

    def __init__(self, config: dict) -> None:
        self.config = config
        self.commands = [
            BotCommand(command='/start', description='Start the dialog with bot'),
            BotCommand(command='/info', description='Invokes information about available commands'),
            BotCommand(command='/stats', description='Показывает статистику по товару'),
            BotCommand(command='/inventory', description='Показывает складские остатки'),
        ]
        self.engine = TelegramBot.__connect_to_db()

    async def start(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        if str(update.message.from_user.id) not in self.config['allowed_user_ids']:
            await update.message.reply_html(
                rf"""Вам запрещён доступ. Свяжитесь с <a href="https://t.me/@denis_selu">@support2</a> для получения большей информации""",
                disable_web_page_preview=True
            )
            return

        start_message = rf"Привет, {update.effective_user.mention_html()}! Я бот для отслеживания складских остатков"

        await update.message.reply_html(
            start_message,
            disable_web_page_preview=True
        )

        await update.message.reply_html(
            rf"Чтобы получить больше информации, отправьте /info",
            disable_web_page_preview=True
        )

    async def info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if str(update.message.from_user.id) not in self.config['allowed_user_ids']:
            await update.message.reply_html(
                rf"""Вам запрещён доступ. Свяжитесь с <a href="https://t.me/@denis_selu">@support2</a> для получения большей информации""",
                disable_web_page_preview=True
            )
            return

        commands = self.commands
        command_data = '\n\n' + '\n'.join([str(command.command + ' - ' + command.description) for command in commands])
        await update.message.reply_html(
            rf"Доступные команды: {command_data}",
            disable_web_page_preview=True
        )

        keyboard = [
            [
                InlineKeyboardButton("Option 1", callback_data="1"),
                InlineKeyboardButton("Option 2", callback_data="2"),
            ],
            [InlineKeyboardButton("Option 3", callback_data="3")],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_html(
            rf"Для дополнительной информации нажмите /help",
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )

    async def inventory(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if str(update.message.from_user.id) not in self.config['allowed_user_ids']:
            await update.message.reply_html(
                rf"""Вам запрещён доступ. Свяжитесь с <a href="https://t.me/@denis_selu">@support2</а> для получения большей информации""",
                disable_web_page_preview=True
            )
            return

        # Загрузка данных из базы данных
        product_name = ' '.join(context.args)
        data = history_remains_for_product(product_name, self.engine)

        # Генерация графика
        tmp_file_path = generate_inventory_chart(data, product_name)

        # Отправка графика пользователю
        with open(tmp_file_path, 'rb') as photo:
            await update.message.reply_photo(photo)

        # Удаление временного файла
        os.remove(tmp_file_path)

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if str(update.message.from_user.id) not in self.config['allowed_user_ids']:
            await update.message.reply_html(
                rf"""Вам запрещён доступ. Свяжитесь с <a href="https://t.me/@denis_selu">@support2</a> для получения большей информации""",
                disable_web_page_preview=True
            )
            return

        # Пример данных для демонстрации
        stats_data = {
            'Дата': ['2023-06-01', '2023-06-02', '2023-06-03', '2023-06-04'],
            'Значение': [10, 15, 7, 20]
        }

        # Генерация графика
        tmp_file_path = generate_stats_chart(stats_data)

        # Отправка графика пользователю
        with open(tmp_file_path, 'rb') as photo:
            await update.message.reply_photo(photo)

        # Удаление временного файла
        os.remove(tmp_file_path)

    async def post_init(self, application: Application) -> None:
        await application.bot.set_my_commands(
            [(botCommand.command, botCommand.description) for botCommand in self.commands])

    def run(self) -> None:
        try:
            application = ApplicationBuilder() \
                .token(self.config['token']) \
                .post_init(self.post_init) \
                .concurrent_updates(True) \
                .build()
        except Exception as e:
            logging.exception(e)
            raise e

        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(CommandHandler("info", self.info))
        application.add_handler(CommandHandler('stats', self.stats))
        application.add_handler(CommandHandler('inventory', self.inventory))

        application.run_polling(allowed_updates=Update.ALL_TYPES)
