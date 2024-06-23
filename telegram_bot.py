
from keycloak import KeycloakOpenID
import os
import logging
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Устанавливаем базовый уровень логирования на DEBUG
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Функция для фильтрации логов, чтобы отображались только DEBUG сообщения
class DebugOnlyFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.DEBUG

# Получаем основной логгер и добавляем к нему фильтр
logger = logging.getLogger()
for handler in logger.handlers:
    handler.addFilter(DebugOnlyFilter())

CHANGE_JSON, FIELD_SELECTION, VALUE_INPUT = range(3)

class TelegramBot:
    def __init__(self, config):
        self.config = config
        self.application = ApplicationBuilder().token(config['token']).build()
        self.authorized_users = {}
        self.pending_auth = {}
        self.counter = 1  # Добавляем счетчик для JSON ID

        self.delete_json_file()

        # Add command handlers
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('change_json', self.change_json_start)],
            states={
                FIELD_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.field_selection)],
                VALUE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.value_input)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        self.application.add_handler(conv_handler)

        self.application.add_handler(CommandHandler('start', self.start))
        self.application.add_handler(CommandHandler('info', self.info))
        self.application.add_handler(CommandHandler('inventory', self.inventory))
        self.application.add_handler(CommandHandler('stats', self.stats))
        self.application.add_handler(CommandHandler('login', self.login))
        self.application.add_handler(CommandHandler('product', self.product))
        self.application.add_handler(CommandHandler('make_json', self.make_json))
        self.application.add_handler(CommandHandler('edit_json', self.edit_json))
        #self.application.add_handler(CommandHandler('change_json', self.change_json_start))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))






        logging.debug("TelegramBot initialized with config and handlers added.")

    async def change_json_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        logging.debug("Starting change_json process.")
        
        if not self.is_user_authorized(update):
            await update.message.reply_text('Сначала необходимо авторизоваться с помощью команды /login.')
            return ConversationHandler.END

        if not os.path.exists('final_answer.json'):
            await update.message.reply_text('Файл JSON не найден. Пожалуйста, сначала сформируйте файл с помощью команды /make_json.')
            return ConversationHandler.END

        try:
            with open('final_answer.json', 'r', encoding='utf-8') as json_file:
                json_data = json.load(json_file)
                logging.debug(f"Loaded JSON data: {json_data}")
        except Exception as e:
            logging.error(f"Failed to load JSON: {str(e)}")
            await update.message.reply_text(f'Ошибка при загрузке JSON: {str(e)}')
            return ConversationHandler.END

        # Получаем ключи из JSON и отображаем пользователю для выбора
        keys = list(json_data.keys())
        logging.debug(f"Available fields in JSON: {keys}")

        if not keys:
            await update.message.reply_text('В JSON файле нет доступных полей для изменения.')
            return ConversationHandler.END

        await update.message.reply_text(
            'Что вы хотите изменить в JSON файле? Выберите одно из полей:',
            reply_markup=ReplyKeyboardMarkup([keys], one_time_keyboard=True)
        )
        logging.debug("Prompted user to select a field.")
        return FIELD_SELECTION


    async def field_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        logging.debug("Entering field_selection state.")
        field = update.message.text
        context.user_data['field'] = field
        logging.debug(f"User selected field: {field}")

        if field == 'rows':
            try:
                with open('final_answer.json', 'r', encoding='utf-8') as json_file:
                    json_data = json.load(json_file)
                    rows = json_data.get('rows', [])
                    if not rows:
                        await update.message.reply_text('Поле rows пустое. Попробуйте снова.')
                        return FIELD_SELECTION

                    row_options = [f"Row {i + 1}: {row['spgzCharacteristics'][0]['characteristicName']}" for i, row in enumerate(rows)]
                    row_options_keyboard = [[KeyboardButton(row_option)] for row_option in row_options]
                    await update.message.reply_text(
                        'Выберите строку для изменения:',
                        reply_markup=ReplyKeyboardMarkup(row_options_keyboard, one_time_keyboard=True)
                    )
                    logging.debug(f"Row options sent to user: {row_options}")
                    return VALUE_INPUT
            except Exception as e:
                logging.error(f"Failed to load JSON: {str(e)}")
                await update.message.reply_text(f'Ошибка при загрузке JSON: {str(e)}')
                return FIELD_SELECTION
        else:
            try:
                with open('final_answer.json', 'r', encoding='utf-8') as json_file:
                    json_data = json.load(json_file)

                    if field in json_data:
                        field_value = json.dumps(json_data[field], indent=4, ensure_ascii=False)
                        if len(field_value) > 4096:  # Проверка длины сообщения
                            field_value = field_value[:4093] + '...'
                        await update.message.reply_text(f'Текущее значение поля {field}:\n{field_value}')
                        logging.debug(f"Field value sent to user: {field_value}")
                    else:
                        await update.message.reply_text(f'Поле {field} не найдено в JSON файле. Попробуйте снова.')
                        logging.debug(f"Field {field} not found in JSON.")
                        return FIELD_SELECTION
                await update.message.reply_text(f'Вы выбрали {field}. Теперь введите новое значение:', reply_markup=ReplyKeyboardRemove())
                logging.debug(f"Prompted user to input new value for field {field}.")
                return VALUE_INPUT
            except Exception as e:
                logging.error(f"Failed to load JSON: {str(e)}")
                await update.message.reply_text(f'Ошибка при загрузке JSON: {str(e)}')
                return FIELD_SELECTION











    async def value_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        field = context.user_data.get('field')
        user_input = update.message.text
        logging.debug(f"User input in value_input: {user_input}")

        if field == 'rows':
            if 'Row' in user_input:
                try:
                    logging.debug(f"Parsing row index from user input: {user_input}")
                    row_number_part = user_input.split(':')[0].strip()
                    if 'Row' in row_number_part:
                        row_index = int(row_number_part.replace('Row', '').strip()) - 1
                        context.user_data['row_index'] = row_index
                        logging.debug(f"User selected row index: {row_index}")
                    else:
                        raise ValueError("No 'Row' keyword found in user input")
                except Exception as e:
                    logging.error(f"Error parsing row index: {str(e)}")
                    await update.message.reply_text('Ошибка при разборе индекса строки. Попробуйте снова.')
                    return VALUE_INPUT

                try:
                    with open('final_answer.json', 'r', encoding='utf-8') as json_file:
                        json_data = json.load(json_file)
                        row_data = json_data['rows'][row_index]
                        row_data_str = json.dumps(row_data, indent=4, ensure_ascii=False)
                        await update.message.reply_text(
                            f'Текущие данные для строки {row_index + 1}:\n{row_data_str}\n\nСкопируйте, измените и отправьте обратно.'
                        )
                        context.user_data['expecting_update'] = True
                        logging.debug(f"Sent row data to user for update: {row_data_str}")
                        return VALUE_INPUT
                except Exception as e:
                    logging.error(f"Failed to load JSON: {str(e)}")
                    await update.message.reply_text(f'Ошибка при загрузке JSON: {str(e)}')
                    return ConversationHandler.END
            else:
                if context.user_data.get('expecting_update'):
                    try:
                        logging.debug(f"Parsing new row value from user input: {user_input}")
                        new_row_value = json.loads(user_input)
                        row_index = context.user_data.get('row_index')
                        with open('final_answer.json', 'r', encoding='utf-8') as json_file:
                            json_data = json.load(json_file)
                            if isinstance(new_row_value, dict):
                                json_data['rows'][row_index] = new_row_value
                            else:
                                await update.message.reply_text('Неверный формат для обновления "rows". Ожидается объект JSON.')
                                logging.debug("Invalid format for row update.")
                                return VALUE_INPUT
                        with open('final_answer.json', 'w', encoding='utf-8') as json_file:
                            json.dump(json_data, json_file, ensure_ascii=False, indent=4)
                        await update.message.reply_text('Строка успешно обновлена.', reply_markup=ReplyKeyboardRemove())
                        await self.send_json_file(chat_id=update.message.chat_id, context=context)
                        context.user_data['expecting_update'] = False
                        logging.debug(f"Row {row_index + 1} updated with new data: {new_row_value}")
                        return ConversationHandler.END
                    except json.JSONDecodeError:
                        await update.message.reply_text('Неверный формат JSON. Попробуйте снова.')
                        logging.debug("JSON decode error.")
                        return VALUE_INPUT
                    except Exception as e:
                        logging.error(f"Failed to update JSON: {str(e)}")
                        await update.message.reply_text(f'Ошибка при обновлении JSON: {str(e)}', reply_markup=ReplyKeyboardRemove())
                        return ConversationHandler.END
                else:
                    await update.message.reply_text('Неверное действие. Попробуйте снова.')
                    return VALUE_INPUT
        else:
            try:
                with open('final_answer.json', 'r', encoding='utf-8') as json_file:
                    json_data = json.load(json_file)
                    json_data[field] = user_input
                with open('final_answer.json', 'w', encoding='utf-8') as json_file:
                    json.dump(json_data, json_file, ensure_ascii=False, indent=4)
                await update.message.reply_text('JSON файл успешно обновлен.', reply_markup=ReplyKeyboardRemove())
                await self.send_json_file(chat_id=update.message.chat_id, context=context)
                return ConversationHandler.END
            except Exception as e:
                logging.error(f"Failed to update JSON: {str(e)}")
                await update.message.reply_text(f'Ошибка при обновлении JSON: {str(e)}', reply_markup=ReplyKeyboardRemove())
                return ConversationHandler.END























    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logging.debug("Received /start command.")
        await update.message.reply_text(
            'Привет! Я бот для автоматизации процесса закупок. Используйте /login для авторизации и доступа к остальным командам.'
        )

    async def info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logging.debug("Received /info command.")
        if not self.is_user_authorized(update):
            await update.message.reply_text('Сначала необходимо авторизоваться с помощью команды /login.')
            return

        await update.message.reply_text(
            'Бот поддерживает следующие команды:\n'
            '/start - Начать диалог\n'
            '/info - Информация о командах\n'
            '/product - Выбор продукта для отображения складских остатков\n'
            '/make_json - Создает JSON файл с закупкой\n'
            '/login - Авторизация через Keycloak\n'
            '/edit_json - Изменить json в WebView\n'
            '/change_json - Изменить JSON через диалог'
        )

    async def edit_json(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logging.debug("Received /edit_json command.")
        if not self.is_user_authorized(update):
            await update.message.reply_text('Сначала необходимо авторизоваться с помощью команды /login.')
            return
        
        if not os.path.exists('final_answer.json'):
            await update.message.reply_text('Файл JSON не найден. Пожалуйста, сначала сформируйте файл с помощью команды /make_json.')
            return

        webapp_url = os.getenv('WEBAPP_URL')
        if not webapp_url:
            await update.message.reply_text('Ошибка конфигурации: URL для WebApp не установлен.')
            return

        if not webapp_url.startswith("https://"):
            await update.message.reply_text('Ошибка конфигурации: URL для WebApp должен начинаться с "https://".')
            return

        await update.message.reply_text(
            'Для редактирования JSON файла перейдите по ссылке ниже:',
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Редактировать JSON", web_app=WebAppInfo(url=f"{webapp_url}/edit_json.html"))]]
            )
        )

    async def product_selected(self, data):
        user_id = data.get('user_id')
        product_name = data.get('product_name')
        image_path = data.get('image_path')
        graph_json = data.get('graph_json')

        import analytics
        try:
            await self.application.bot.send_photo(chat_id=user_id, photo=open(image_path, 'rb'))
            values = analytics.history_remains_for_product(product_name, analytics.get_database_connection())
            values_text = '\n'.join([f'{date}: {value}' for date, value in values.items()])
            await self.application.bot.send_message(chat_id=user_id, text=f"Остатки для продукта {product_name}:\n{values_text}")
        except ValueError as e:
            logging.error(f"No data for product: {str(e)}")
            await self.application.bot.send_message(chat_id=user_id, text=f"Нет данных для продукта: {str(e)}")
        except RuntimeError as e:
            logging.error(f"SQL execution error: {str(e)}")
            await self.application.bot.send_message(chat_id=user_id, text=f"Ошибка при выполнении SQL запроса: {str(e)}")
        except Exception as e:
            logging.error(f"Failed to generate inventory chart: {str(e)}")
            await self.application.bot.send_message(chat_id=user_id, text=f"Ошибка при генерации графика для продукта: {str(e)}")


    async def login(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logging.debug("Received /login command.")
        self.pending_auth[update.message.from_user.id] = {'stage': 'username'}
        await update.message.reply_text('Пожалуйста, введите ваше имя пользователя.')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.message.from_user.id
        if user_id in self.pending_auth:
            stage = self.pending_auth[user_id].get('stage')

            if stage == 'username':
                self.pending_auth[user_id]['username'] = update.message.text
                self.pending_auth[user_id]['stage'] = 'password'
                await update.message.reply_text('Теперь введите ваш пароль.')

            elif stage == 'password':
                self.pending_auth[user_id]['password'] = update.message.text
                await self.authenticate_user(update, context)
            
            elif stage == 'product_name':
                product_name = update.message.text
                logging.debug(f"Received product name: {product_name}")
                import analytics
                try:
                    image_path, graph_json = analytics.generate_inventory_for_product(product_name)
                    await update.message.reply_photo(photo=open(image_path, 'rb'))
                except Exception as e:
                    logging.error(f"Failed to generate inventory chart: {str(e)}")
                    await update.message.reply_text(f"Ошибка при генерации графика для продукта: {str(e)}")
                del self.pending_auth[user_id]

    async def authenticate_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.message.from_user.id
        username = self.pending_auth[user_id]['username']
        password = self.pending_auth[user_id]['password']
        
        keycloak_openid = KeycloakOpenID(
            server_url=os.getenv('KEYCLOAK_SERVER_URL'),
            client_id=os.getenv('KEYCLOAK_CLIENT_ID'),
            realm_name=os.getenv('KEYCLOAK_REALM_NAME'),
            client_secret_key=os.getenv('KEYCLOAK_CLIENT_SECRET'),
            verify=False  # Отключение проверки SSL
        )
        
        try:
            token = keycloak_openid.token(
                username=username,
                password=password,
                grant_type='password'
            )
            self.authorized_users[update.message.from_user.id] = True
            del self.pending_auth[update.message.from_user.id]
            await update.message.reply_text('Авторизация успешна! Теперь вам доступны все команды. Используйте /info для получения списка команд.')
        except Exception as e:
            logging.error(f"Failed to get Keycloak token: {str(e)}")
            del self.pending_auth[user_id]
            await update.message.reply_text(f"Авторизация не удалась: {str(e)}. Попробуйте снова с помощью команды /login.")

    async def inventory(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logging.debug("Received /inventory command.")
        if not self.is_user_authorized(update):
            await update.message.reply_text('Сначала необходимо авторизоваться с помощью команды /login.')
            return

        import analytics
        data = {'Товар': ['Товар1', 'Товар2'], 'Количество': [10, 20]}
        chart_path = analytics.generate_inventory_chart(data, 'Sample Product')
        await update.message.reply_photo(photo=open(chart_path, 'rb'))

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logging.debug("Received /stats command.")
        if not self.is_user_authorized(update):
            await update.message.reply_text('Сначала необходимо авторизоваться с помощью команды /login.')
            return

        import analytics
        data = {'Дата': ['2024-01-01', '2024-02-01'], 'Значение': [100, 200]}
        chart_path = analytics.generate_stats_chart(data)
        await update.message.reply_photo(photo=open(chart_path, 'rb'))

    async def product(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logging.debug("Received /product command.")
        if not self.is_user_authorized(update):
            await update.message.reply_text('Сначала необходимо авторизоваться с помощью команды /login.')
            return

        webapp_url = os.getenv('WEBAPP_URL')
        if not webapp_url:
            await update.message.reply_text('Ошибка конфигурации: URL для WebApp не установлен.')
            return

        if not webapp_url.startswith("https://"):
            await update.message.reply_text('Ошибка конфигурации: URL для WebApp должен начинаться с "https://".')
            return

        await update.message.reply_text(
            'Для выбора продукта перейдите по ссылке ниже:',
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Выбор продукта", web_app=WebAppInfo(url=f"{webapp_url}/products.html"))]]
            )
        )

    async def product_selected(self, data):
        user_id = data.get('user_id')
        product_name = data.get('product_name')
        image_path = data.get('image_path')

        import analytics
        try:
            await self.application.bot.send_photo(chat_id=user_id, photo=open(image_path, 'rb'))
            values = analytics.history_remains_for_product(product_name, analytics.get_database_connection())
            values_text = '\n'.join([f'{date}: {value}' for date, value in values.items()])
            await self.application.bot.send_message(chat_id=user_id, text=f"Остатки для продукта {product_name}:\n{values_text}")
        except ValueError as e:
            logging.error(f"No data for product: {str(e)}")
            await self.application.bot.send_message(chat_id=user_id, text=f"Нет данных для продукта: {str(e)}")
        except RuntimeError as e:
            logging.error(f"SQL execution error: {str(e)}")
            await self.application.bot.send_message(chat_id=user_id, text=f"Ошибка при выполнении SQL запроса: {str(e)}")
        except Exception as e:
            logging.error(f"Failed to generate inventory chart: {str(e)}")
            await self.application.bot.send_message(chat_id=user_id, text=f"Ошибка при генерации графика для продукта: {str(e)}")

    async def make_json(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self.is_user_authorized(update):
            await update.message.reply_text('Сначала необходимо авторизоваться с помощью команды /login.')
            return
        await update.message.reply_text('Формирование JSON файла. Пожалуйста, подождите...')

        import analytics
        engine = analytics.get_database_connection()
        products = analytics.all_regular_product_names(engine)

        final_answer = {}

        final_answer['id'] = int(self.counter)  # уникальный номер
        final_answer['lotEntityId'] = 0  # не надо
        final_answer['CustomerId'] = str(update.message.from_user.id)  # telegram id кто писал
        final_answer['rows'] = []
        for product_name in products:
            cnt_to_buy, sum_to_buy = analytics.get_cnt_sum(product_name, engine)
            if isinstance(cnt_to_buy, list) and isinstance(sum_to_buy, list) and cnt_to_buy and sum_to_buy:
                final_answer['rows'].append(analytics.make_one_row(product_name, cnt_to_buy[0], sum_to_buy[0], engine))

        tmp_json_filename = 'final_answer.json'
        try:
            with open(tmp_json_filename, 'w', encoding='utf-8') as json_file:
                json.dump(final_answer, json_file, ensure_ascii=False, indent=4)
                logging.debug(f"JSON file created: {tmp_json_filename}")

            # Проверка наличия файла
            if not os.path.exists(tmp_json_filename):
                logging.error(f"File not found: {tmp_json_filename}")
                await update.message.reply_text(f"Ошибка: файл {tmp_json_filename} не найден.")
                return

            # Отправим JSON файл через Telegram-бота
            with open(tmp_json_filename, 'rb') as json_file:
                await context.bot.send_document(chat_id=update.message.chat_id, document=json_file)

            #os.remove(tmp_json_filename)
        except Exception as e:
            logging.error(f"Error while creating or sending JSON file: {str(e)}")
            await update.message.reply_text(f"Ошибка при создании или отправке JSON файла: {str(e)}")

        self.counter += 1


    async def send_json_file(self, chat_id, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            tmp_json_filename = 'final_answer.json'
            if os.path.exists(tmp_json_filename):
                with open(tmp_json_filename, 'rb') as json_file:
                    await context.bot.send_document(chat_id=chat_id, document=json_file)
            else:
                logging.error(f"File not found: {tmp_json_filename}")
        except Exception as e:
            logging.error(f"Error while sending JSON file: {str(e)}")

    async def inventory(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logging.debug("Received /inventory command.")
        if not self.is_user_authorized(update):
            await update.message.reply_text('Сначала необходимо авторизоваться с помощью команды /login.')
            return

        import analytics
        engine = analytics.get_database_connection()
        products = analytics.get_unique_products()

        if not products:
            await update.message.reply_text('Нет доступных продуктов.')
            return

        await update.message.reply_text(
            'Список доступных продуктов:\n' + '\n'.join(products)
        )


    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text('Отмена операции.', reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    
    def is_user_authorized(self, update: Update) -> bool:
        user_id = update.message.from_user.id
        return self.authorized_users.get(user_id, False)
    
    def delete_json_file(self):
        try:
            if os.path.exists('final_answer.json'):
                os.remove('final_answer.json')
                logging.debug("Existing JSON file deleted.")
            else:
                logging.debug("No JSON file found to delete.")
        except Exception as e:
            logging.error(f"Error while deleting JSON file: {str(e)}")


    def run(self):
        logging.debug("Starting bot polling.")
        self.application.run_polling()

if __name__ == "__main__":
    import threading

    config = {
        'token': os.getenv('TELEGRAM_TOKEN')
    }

    bot = TelegramBot(config)

    # Запуск Flask в отдельном потоке и передача объекта bot
    from webapp import WebApp
    web_app = WebApp(bot)  # Передаем объект bot
    flask_thread = threading.Thread(target=web_app.run)
    flask_thread.start()

    bot.run()

