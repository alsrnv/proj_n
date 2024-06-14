
from __future__ import annotations

import os
import json
import logging
import asyncio
import traceback
import requests
import subprocess

from telegram import ForceReply, Update, BotCommand, \
    InlineQueryResultArticle, InputTextMessageContent, \
    InlineKeyboardButton, InlineKeyboardMarkup, \
    KeyboardButton,ReplyKeyboardMarkup, ReplyKeyboardRemove, \
    WebAppInfo, BotCommandScopeChat, BotCommandScopeDefault, \
    InlineQueryResultArticle, BotCommandScopeAllGroupChats, constants, \
    LabeledPrice
from telegram.constants import ParseMode
from telegram.error import RetryAfter, TimedOut
from telegram.ext import filters, MessageHandler, CommandHandler, Application, ApplicationBuilder, ContextTypes, \
    InlineQueryHandler, CallbackQueryHandler, CallbackContext, PreCheckoutQueryHandler, ConversationHandler

from html import escape
from uuid import uuid4

# from utils import is_group_chat, get_thread_id, message_text, wrap_with_indicator, split_into_chunks, \
#     edit_message_with_retry, get_stream_cutoff_values, is_allowed, is_admin, \
#     get_reply_to_message_id, add_chat_request_to_usage_tracker, error_handler, is_direct_result, handle_direct_result, \
#     cleanup_intermediate_files
from icecream import ic


START_ROUTES, END_ROUTES = range(2)


class TelegramBot:
   

    def __init__(self, config: dict) -> None:
       

        # Store the bot configuration
        self.config = config

        # Set up the bot localization
        # bot_language = self.config['bot_language']

        # Set up the bot commands
        self.commands = [
            BotCommand(command='/start', description='start the dialog with bot'),
            BotCommand(command='ℹ️ /info', description='invokes information about available commands'),
            BotCommand(command='📊 /stats', description='Показывает статистику по товару'),
        ]
        self.disallowed_message = 'disallowed'
        self.usage = {}
        self.last_message = {}
        self.inline_queries_cache = {}


    async def start(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the start command.
        """
        # Check if the user is allowed to use the bot
        if str(update.message.from_user.id) not in self.config['allowed_user_ids']:
            await update.message.reply_html(
            rf"""Вам запрещён доступ. Свяжитесь с <a href="https://t.me/@denis_selu">@support2</a> для получения большей информации""",
            disable_web_page_preview=True
            )
            return

        start_message = rf"Привет, {update.effective_user.mention_html()}!  Я бот для отслеживания складских остатков"
        # 

        await update.message.reply_html(
            start_message,
            # reply_markup=ForceReply(selective=True),
            disable_web_page_preview=True
        )

        await update.message.reply_html(
            rf"Чтобы получить больше информации, отправьте /info",
            disable_web_page_preview=True
        )

    async def info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Sends information about the bot.
        """
        # Check if the user is allowed to use the bot
        if str(update.message.from_user.id) not in self.config['allowed_user_ids']:
            await update.message.reply_html(
            rf"""Вам запрещён доступ. Свяжитесь с <a href="https://t.me/@denis_selu">@support2</a> для получения большей информации""",
            disable_web_page_preview=True
            )
            return

        commands = self.commands
        command_data = '\n\n'+'\n'.join([str(command['command']+' - '+command['description']) for command in commands])
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


    async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Parses the CallbackQuery and updates the message text."""
        query = update.callback_query

        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
        await query.answer()

        await query.edit_message_text(text=f"Selected option: {query.data}")


    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Returns token usage statistics for current day and month.
        """
        # Check if the user is allowed to use the bot
        if str(update.message.from_user.id) not in self.config['allowed_user_ids']:
            await update.message.reply_html(
            rf"""Вам запрещён доступ. Свяжитесь с <a href="https://t.me/@denis_selu">@support2</a> для получения большей информации""",
            disable_web_page_preview=True
            )
            return

        
        # await update.message.reply_html(
        #     rf"Статистика. Выберите текст или картинку",
        #     disable_web_page_preview=True
        # )
        keyboard = [
            [
                InlineKeyboardButton("Картинка", callback_data="pic"),
                InlineKeyboardButton("JSON", callback_data="json"),
            ],
            # [InlineKeyboardButton("Option 3", callback_data="3")],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_html(
            rf"Статистика. Выберите текст или картинку",
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )
        print("HERE!\n")
        if update.answer_callback_query != None:
            callback_query_id = update.callback_query.id
            data = update.callback_query.data.encode('utf-8').decode()
            print("HELLOOOO\n")
            # self.info(update, context)
            await update.message.reply_html(
                rf"Статистика. Текст",
                disable_web_page_preview=True,
            )
                # await update.message.reply_text("Статистика", reply_markup=keyboard)
        

    
    async def post_init(self, application: Application) -> None:
        """
        Post initialization hook for the bot.
        """
        await application.bot.set_my_commands([(botCommand.command.split('/')[1], botCommand.description) for botCommand in self.group_commands])
        await application.bot.set_my_commands([(botCommand.command.split('/')[1], botCommand.description) for botCommand in self.commands])

    
    async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Returns `ConversationHandler.END`, which tells the
        ConversationHandler that the conversation is over.
        """
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text="See you next time!")
        return ConversationHandler.END


    async def start_over(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Prompt same text & keyboard as `start` does but not as new message"""
        # Get CallbackQuery from Update
        query = update.callback_query
        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
        await query.answer()
        keyboard = [
            [
                InlineKeyboardButton("1", callback_data=str(ONE)),
                InlineKeyboardButton("2", callback_data=str(TWO)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Instead of sending a new message, edit the message that
        # originated the CallbackQuery. This gives the feeling of an
        # interactive menu.
        await query.edit_message_text(text="Start handler, Choose a route", reply_markup=reply_markup)
        return START_ROUTES

    def run(self) -> None:
        """
        Runs the bot indefinitely until the user presses Ctrl+C
        """

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
       
        application.run_polling(allowed_updates=Update.ALL_TYPES)
