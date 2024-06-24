
# Telegram Bot для автоматизации закупок

Этот проект представляет собой Telegram бот, предназначенный для автоматизации процессов закупок. Бот позволяет авторизованным пользователям выполнять различные задачи, такие как просмотр статистики складских запасов, выбор продуктов, генерация JSON файлов с данными по закупкам и редактирование этих JSON файлов через веб-интерфейс.

## Функциональность

1. **Аутентификация**: Использует Keycloak для аутентификации пользователей.
2. **Статистика складских запасов**: Генерирует и отображает статистику и графики по складским запасам.
3. **Выбор продуктов**: Позволяет пользователям выбирать продукты через веб-интерфейс.
4. **Генерация JSON файлов**: Генерирует JSON файлы с данными по закупкам.
5. **Редактирование JSON файлов**: Предоставляет веб-интерфейс (а также диалог) для редактирования сгенерированных JSON файлов.
6. **Прогноз закупов**: Предоставляет инструмент для прогнозирования регулярных товаров.

## Команды

- `/start`: Начинает диалог с ботом.
- `/info`: Предоставляет информацию о доступных командах.
- `/login`: Запускает процесс аутентификации.
- `/product`: Позволяет выбрать продукт через веб-интерфейс.
- `/make_json`: Генерирует JSON файл с данными по закупкам.
- `/edit_json`: Открывает веб-интерфейс для редактирования JSON файла.
- `/change_json`: Позволяет редактировать JSON файл в диалоге (без веб-интерфейса).
- `/make_prediction`: Делает прогноз для выбранного регулярного товара и периода.

## Переменные окружения

Для корректной работы бота и веб-приложения необходимо установить следующие переменные окружения:

- `TELEGRAM_TOKEN`: Токен вашего Telegram бота.
- `DATABASE_URL`: URL для подключения к вашей базе данных.
- `KEYCLOAK_SERVER_URL`: URL вашего сервера Keycloak.
- `KEYCLOAK_CLIENT_ID`: Идентификатор клиента для Keycloak.
- `KEYCLOAK_REALM_NAME`: Название области (realm) для Keycloak.
- `KEYCLOAK_CLIENT_SECRET`: Секретный ключ клиента для Keycloak.
- `FLASK_SECRET_KEY`: Секретный ключ для сессий Flask.
- `WEBAPP_URL`: Базовый URL для веб-приложения.

## Установка

1. **Клонируйте репозиторий**:
   ```bash
   git clone https://github.com/alsrnv/proj_n
   cd proj_n
   ```

2. **Установите зависимости**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Установите переменные окружения**:
   Создайте файл `.env` в корне проекта и добавьте следующие строки:
   ```bash
   TELEGRAM_TOKEN=your_telegram_token
   DATABASE_URL=your_database_url
   KEYCLOAK_SERVER_URL=your_keycloak_server_url
   KEYCLOAK_CLIENT_ID=your_keycloak_client_id
   KEYCLOAK_REALM_NAME=your_keycloak_realm_name
   KEYCLOAK_CLIENT_SECRET=your_keycloak_client_secret
   FLASK_SECRET_KEY=your_flask_secret_key
   WEBAPP_URL=your_webapp_url
   ```

4. **Запустите бота и веб-приложение**:
   ```bash
   python telegram_bot.py
   ```

## 1. Установка в Docker

1. **Клонируйте репозиторий**:
   ```bash
   git clone https://github.com/alsrnv/proj_n
   cd proj_n
   ```

2. **Создайте файл `.env` в корне проекта и добавьте переменные окружения** (см. выше).

3. **Постройте Docker образ**:
   ```bash
   docker build -t telegram-bot-procurement .
   ```

4. **Запустите контейнер**:
   ```bash
   docker run --env-file .env -p 5000:5000 telegram-bot-procurement
   ```

## 2. Описание файлов

### 2.1. `telegram_bot.py`

Этот файл содержит основную логику для Telegram бота, включая обработчики команд и аутентификацию пользователей.

- **Класс `TelegramBot`**:
  - `__init__(self, config)`: Инициализирует бота с заданной конфигурацией.
  - `start(self, update: Update, context: ContextTypes.DEFAULT_TYPE)`: Обрабатывает команду `/start`.
  - `info(self, update: Update, context: ContextTypes.DEFAULT_TYPE)`: Обрабатывает команду `/info`.
  - `login(self, update: Update, context: ContextTypes.DEFAULT_TYPE)`: Обрабатывает команду `/login`.
  - `handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE)`: Обрабатывает текстовые сообщения.
  - `authenticate_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE)`: Аутентифицирует пользователя с использованием Keycloak.
  - `inventory(self, update: Update, context: ContextTypes.DEFAULT_TYPE)`: Обрабатывает команду `/inventory`.
  - `stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE)`: Обрабатывает команду `/stats`.
  - `product(self, update: Update, context: ContextTypes.DEFAULT_TYPE)`: Обрабатывает команду `/product`.
  - `product_selected(self, data)`: Обрабатывает выбор продукта.
  - `make_json(self, update: Update, context: ContextTypes.DEFAULT_TYPE)`: Обрабатывает команду `/make_json`, генерирует и отправляет JSON файл.
  - `edit_json(self, update: Update, context: ContextTypes.DEFAULT_TYPE)`: Обрабатывает команду `/edit_json`, открывает веб-интерфейс для редактирования JSON файла.
  - `is_user_authorized(self, update: Update)`: Проверяет, авторизован ли пользователь.
  - `run(self)`: Запускает бота.

### 2.2. `webapp.py`

Этот файл содержит логику для веб-приложения, включая маршрутизацию и обработку запросов.

- **Класс `WebApp`**:
  - `__init__(self, bot)`: Инициализирует веб-приложение с заданным ботом.
  - `setup_routes(self)`: Настраивает маршруты для веб-приложения.
  - `serve_login_page(self)`: Обрабатывает запросы к `/login.html`.
  - `serve_products_page(self)`: Обрабатывает запросы к `/products.html`.
  - `get_products(self)`: Обрабатывает запросы к `/get_products`.
  - `product_selection(self)`: Обрабатывает запросы к `/product_selection`.
  - `serve_edit_json_page(self)`: Обрабатывает запросы к `/edit_json.html`.
  - `get_json(self)`: Обрабатывает запросы к `/get_json`.
  - `update_json(self)`: Обрабатывает запросы к `/update_json`.
  - `run(self)`: Запускает Flask сервер.

### 2.3. `analytics.py`

Этот файл содержит функции для анализа данных, генерации графиков и JSON файлов.

- `day_of_quarter(quarter, day_type, year='2022')`: Определяет первый или последний день квартала.
- `get_database_connection()`: Устанавливает соединение с базой данных.
- `history_remains_for_product(product_name, engine)`: Получает историю остатков товара.
- `make_kpgz_spgz_ste(product_name, engine)`: Возвращает данные из таблицы `reference_data` для заданного товара.
- `make_contracts(product_name, engine)`: Возвращает данные из таблицы `contracts` для заданного товара.
- `all_distinct_products(engine)`: Возвращает список всех уникальных товаров.
- `get_unique_products()`: Возвращает список уникальных продуктов из таблицы `inventory_balances`.
- `generate_stats_chart(stats_data)`: Генерирует график для статистических данных.
- `generate_inventory_chart(data, product_name)`: Генерирует график для складских запасов.
- `generate_inventory_for_product(product_name)`: Генерирует график для заданного товара.
- `make_one_row(product_name, cnt_to_buy, sum_to_buy, engine)`: Создает одну строку данных для JSON файла.
- `exponential_smoothing(series, alpha)`: Применяет экспоненциальное сглаживание к временному ряду.
- `get_cnt_sum(product_name: str, engine)`: Получает количество и сумму для закупки товара.
- `make_financial_data(product_name, engine)`: Возвращает финансовые данные для заданного товара.
- `make_json_file(engine, user_id)`: Генерирует JSON файл с данными по закупкам.

## 3. Примечания

- Убедитесь, что все переменные окружения правильно настроены.
- Запускать бота и веб-приложение можно командой `python telegram_bot.py`.
- Убедитесь, что у вас установлены все зависимости, указанные в `requirements.txt`.
- Для запуска в Docker используйте команды, описанные выше.
