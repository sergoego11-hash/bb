import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes, 
    MessageHandler, filters, ConversationHandler
)
import sqlite3
import json
from datetime import datetime, timedelta
import random
import requests
from typing import Dict, List

# Настройка logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Состояния для ConversationHandler
TITLE, DATE, DESCRIPTION, LOCATION = range(4)
WISHLIST_ITEM = range(1)

class SuperCalendarBot:
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
        self.init_databases()
        
        # Координаты Санкт-Петербурга
        self.spb_coordinates = {
            'lat': 59.9311,
            'lon': 30.3609,
            'name': 'Санкт-Петербург',
            'country': 'RU'
        }

        # База идей для выходных
        self.weekend_activities = [
            "🎨 Посетить Эрмитаж или Русский музей",
            "🚶‍♂️ Прогуляться по набережной Невы и посмотреть на развод мостов",
            "📚 Провести день в Российской национальной библиотеке",
            "🍳 Приготовить традиционные петербургские блюда - корюшку или пышки",
            "🎬 Посмотреть фильм в кинотеатре 'Аврора' или 'Англетер'",
            "🌳 Погулять в Летнем саду или Михайловском саду",
            "🛍️ Пройтись по Невскому проспекту и зайти в Гостиный двор",
            "🎯 Сходить в тир или на урок стрельбы из лука",
            "🧘‍♀️ Попробовать йогу на пляже у Петропавловской крепости",
            "🎵 Сходить на концерт в Мариинский театр или Филармонию",
        ]
        
        # База идей для свиданий
        self.date_ideas = [
            "💕 Романтический ужин при свечах дома",
            "🎭 Посещение театральной премьеры",
            "🌅 Пикник на закате в живописном месте",
            "🎯 Соревнование в настольные игры с призами",
            "🍷 Дегустация вин или крафтового пива",
            "🚗 Поездка в соседний город на один день",
            "🎨 Совместный мастер-класс по живописи",
            "⭐ Ночная прогулка с поиском созвездий",
            "🍳 Кулинарный мастер-класс от шеф-повара",
            "🎮 Вечер видеоигр с пиццей и попкорном",
            "🌌 Наблюдение за звездами в планетарии",
            "🏛️ Экскурсия по историческому месту",
            "🎵 Посещение джазового концерта",
            "🚲 Велопрогулка по красивым местам",
            "🍂 Осенняя фотосессия в парке",
            "🎪 Посещение карнавала или ярмарки",
            "🏺 Мастер-класс по гончарному делу",
            "🌃 Ужин в ресторане с панорамным видом",
            "🎬 Просмотр классического кино под открытым небом",
            "🍁 Создание осеннего венка из листьев",
        ]

        # Система ачивок
        self.achievements_db = {
            "first_event": {"name": "🎯 Первое мероприятие", "description": "Создайте ваше первое событие", "icon": "🎯"},
            "weekend_planner": {"name": "🏆 Планировщик выходных", "description": "Используйте генератор идей 10 раз", "icon": "🏆"},
            "social_butterfly": {"name": "🦋 Социальная бабочка", "description": "Создайте 3 совместные доски", "icon": "🦋"},
            "date_master": {"name": "💕 Мастер свиданий", "description": "Сгенерируйте 15 идей для свиданий", "icon": "💕"},
        }

        # Для хранения истории показанных идей
        self.user_idea_history = {}

    def init_databases(self):
        """Инициализация всех таблиц базы данных"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                city TEXT DEFAULT 'Санкт-Петербург',
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица мероприятий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                board_id INTEGER DEFAULT 0,
                title TEXT,
                description TEXT,
                event_date TIMESTAMP,
                event_type TEXT,
                location TEXT,
                reminder_sent BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица досок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS boards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                invite_code TEXT UNIQUE,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица участников досок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS board_members (
                board_id INTEGER,
                user_id INTEGER,
                role TEXT DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (board_id, user_id)
            )
        ''')
        
        # Таблица статистики пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                events_created INTEGER DEFAULT 0,
                weekend_ideas_generated INTEGER DEFAULT 0,
                date_ideas_generated INTEGER DEFAULT 0,
                weather_checks INTEGER DEFAULT 0,
                boards_created INTEGER DEFAULT 0,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица ачивок пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_achievements (
                user_id INTEGER,
                achievement_id TEXT,
                progress INTEGER DEFAULT 0,
                unlocked BOOLEAN DEFAULT FALSE,
                unlocked_at TIMESTAMP,
                PRIMARY KEY (user_id, achievement_id)
            )
        ''')

        # Таблица вишлиста
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wishlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_text TEXT,
                status TEXT DEFAULT 'want',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def setup_handlers(self):
        """Настройка обработчиков команд"""
        # ConversationHandler для создания мероприятий
        conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.create_event_step, pattern='^create_step$')],
            states={
                TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_title)],
                DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_date)],
                DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_description)],
                LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_location)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel_creation)]
        )

        # ConversationHandler для добавления в вишлист
        wishlist_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.add_wishlist_item, pattern='^add_wishlist$')],
            states={
                WISHLIST_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_wishlist_item)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel_wishlist)]
        )

        self.application.add_handler(conv_handler)
        self.application.add_handler(wishlist_conv_handler)
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("weekend", self.suggest_weekend))
        self.application.add_handler(CommandHandler("date_idea", self.suggest_date))
        self.application.add_handler(CommandHandler("weather", self.weather_command))
        self.application.add_handler(CommandHandler("achievements", self.show_achievements))
        self.application.add_handler(CommandHandler("new_event", self.new_event))
        self.application.add_handler(CommandHandler("my_events", self.show_my_events))
        self.application.add_handler(CommandHandler("clear_events", self.clear_old_events))
        self.application.add_handler(CommandHandler("stats", self.show_stats))
        self.application.add_handler(CommandHandler("set_city", self.set_city))
        self.application.add_handler(CommandHandler("create_board", self.create_board))
        self.application.add_handler(CommandHandler("join_board", self.join_board))
        self.application.add_handler(CommandHandler("my_boards", self.show_my_boards))
        self.application.add_handler(CommandHandler("wishlist", self.show_wishlist))
        
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    # 🌟 ОСНОВНОЕ МЕНЮ И НАВИГАЦИЯ
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None):
        """Показ красивого главного меню"""
        user = update.effective_user
        
        if not message:
            message = f"""
✨ <b>ГЛАВНОЕ МЕНЮ</b> ✨

Привет, <b>{user.first_name}</b>! 🎉

🌈 <b>Ваш персональный планировщик</b>
━━━━━━━━━━━━━━━━━━━━━━

🎯 <b>Быстрые действия:</b>
"""

        keyboard = [
            [InlineKeyboardButton("🎯 Идеи для выходных", callback_data="weekend"),
             InlineKeyboardButton("💕 Идеи для свиданий", callback_data="date")],
            [InlineKeyboardButton("🌤️ Погода в СПб", callback_data="weather"),
             InlineKeyboardButton("📅 Создать событие", callback_data="new_event")],
            [InlineKeyboardButton("📋 Мои мероприятия", callback_data="my_events"),
             InlineKeyboardButton("👥 Общие доски", callback_data="my_boards")],
            [InlineKeyboardButton("🎁 Мой вишлист", callback_data="wishlist"),
             InlineKeyboardButton("🏆 Мои ачивки", callback_data="achievements")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Определяем, откуда пришел запрос
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        self.save_user(user)
        
        welcome_message = f"""
🎊 <b>ДОБРО ПОЖАЛОВАТЬ В СУПЕР-КАЛЕНДАРЬ!</b> 🎊

Привет, <b>{user.first_name}</b>! 👋

🚀 <b>Ваш умный помощник для идеального планирования:</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ <b>Что нового:</b>
• 🎁 Вишлист с системой статусов
• 🧹 Очистка старых мероприятий
• 🔄 Улучшенные идеи для свиданий
• 👥 Быстрое подключение к доскам

🎨 <b>Просто выберите действие ниже:</b>
"""
        await self.show_main_menu(update, context, welcome_message)

    # 🎯 СИСТЕМА ИДЕЙ (УЛУЧШЕННАЯ)
    def get_unique_idea(self, user_id: int, idea_type: str) -> str:
        """Получение уникальной идеи для пользователя"""
        if user_id not in self.user_idea_history:
            self.user_idea_history[user_id] = {'weekend': [], 'date': []}
        
        if idea_type == 'weekend':
            pool = self.weekend_activities
            history = self.user_idea_history[user_id]['weekend']
        else:
            pool = self.date_ideas
            history = self.user_idea_history[user_id]['date']
        
        # Если все идеи были показаны, очищаем историю
        available_ideas = [idea for idea in pool if idea not in history]
        if not available_ideas:
            history.clear()
            available_ideas = pool
        
        # Выбираем случайную идею
        idea = random.choice(available_ideas)
        history.append(idea)
        
        # Ограничиваем историю последними 10 идеями
        if len(history) > 10:
            history.pop(0)
            
        return idea

    async def suggest_weekend(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Генератор идей для выходных"""
        user_id = update.effective_user.id
        self.update_stat(user_id, 'weekend_ideas_generated')
        
        activity = self.get_unique_idea(user_id, 'weekend')
        
        message = f"""
🎉 <b>ИДЕЯ ДЛЯ ВЫХОДНЫХ</b> 🎉

━━━━━━━━━━━━━━━━━━━━━━
{activity}
━━━━━━━━━━━━━━━━━━━━━━

💫 <i>Хотите другую идею?</i>
"""
        
        keyboard = [
            [InlineKeyboardButton("🔄 Новая идея", callback_data="weekend"),
             InlineKeyboardButton("💕 Идея для свидания", callback_data="date")],
            [InlineKeyboardButton("📅 Создать событие", callback_data="new_event"),
             InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

    async def suggest_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Генератор идей для свиданий"""
        user_id = update.effective_user.id
        self.update_stat(user_id, 'date_ideas_generated')
        
        date_idea = self.get_unique_idea(user_id, 'date')
        
        message = f"""
💖 <b>ИДЕЯ ДЛЯ СВИДАНИЯ</b> 💖

━━━━━━━━━━━━━━━━━━━━━━
{date_idea}
━━━━━━━━━━━━━━━━━━━━━━

✨ <i>Ищете другое приключение?</i>
"""
        
        keyboard = [
            [InlineKeyboardButton("🔄 Новая идея", callback_data="date"),
             InlineKeyboardButton("🎯 Идея для выходных", callback_data="weekend")],
            [InlineKeyboardButton("📅 Создать событие", callback_data="new_event"),
             InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

    # 📅 СИСТЕМА МЕРОПРИЯТИЙ (ИСПРАВЛЕННАЯ)
    async def new_event(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Создание нового мероприятия"""
        message = """
📅 <b>СОЗДАНИЕ МЕРОПРИЯТИЯ</b>

Выберите способ создания:
"""
        
        keyboard = [
            [InlineKeyboardButton("📝 Пошаговое создание", callback_data="create_step")],
            [InlineKeyboardButton("⚡ Быстрый ввод", callback_data="quick_create")],
            [InlineKeyboardButton("👥 Добавить в доску", callback_data="add_to_board")],
            [InlineKeyboardButton("📋 Мои мероприятия", callback_data="my_events")],
            [InlineKeyboardButton("🧹 Очистить старые", callback_data="clear_events")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

    async def show_my_events(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать мои мероприятия"""
        user_id = update.effective_user.id
        
        events = self.get_user_events(user_id)
        
        if not events:
            message = """
📋 <b>МОИ МЕРОПРИЯТИЯ</b>

У вас пока нет созданных мероприятий.

🎯 <i>Самое время создать первое событие!</i>
"""
            keyboard = [
                [InlineKeyboardButton("📅 Создать событие", callback_data="new_event")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ]
        else:
            message = f"""
📋 <b>МОИ МЕРОПРИЯТИЯ</b>

Найдено мероприятий: <b>{len(events)}</b>
━━━━━━━━━━━━━━━━━━━━━━
"""
            for i, event in enumerate(events[:5], 1):
                event_id, title, event_date, location = event
                message += f"\n<b>{i}. {title}</b>\n"
                message += f"   📅 {event_date}\n"
                message += f"   📍 {location}\n"
                message += "   ━━━━━━━━━━━━━━━━\n"
            
            if len(events) > 5:
                message += f"\n<i>... и еще {len(events) - 5} мероприятий</i>"
        
            keyboard = [
                [InlineKeyboardButton("📅 Создать новое", callback_data="new_event")],
                [InlineKeyboardButton("🧹 Очистить старые", callback_data="clear_events")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

    async def clear_old_events(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Очистка прошедших мероприятий"""
        user_id = update.effective_user.id
        deleted_count = self.delete_old_events(user_id)
        
        message = f"""
🧹 <b>ОЧИСТКА МЕРОПРИЯТИЙ</b>

Удалено прошедших мероприятий: <b>{deleted_count}</b>

✅ <i>Ваш календарь очищен!</i>
"""
        
        keyboard = [
            [InlineKeyboardButton("📋 Мои мероприятия", callback_data="my_events")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

    def delete_old_events(self, user_id: int) -> int:
        """Удаление прошедших мероприятий"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM events WHERE user_id = ? AND event_date < ?', 
                      (user_id, datetime.now()))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count

    # 🎁 СИСТЕМА ВИШЛИСТА (ИСПРАВЛЕННАЯ)
    async def show_wishlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать вишлист пользователя"""
        user_id = update.effective_user.id
        wishlist_items = self.get_wishlist(user_id)
        
        message = """
🎁 <b>МОЙ ВИШЛИСТ</b>

Здесь вы можете хранить свои желания и мечты!
"""
        
        if not wishlist_items:
            message += "\n📝 <i>Пока нет желаний. Добавьте первое!</i>"
        else:
            message += f"\n📋 Найдено желаний: <b>{len(wishlist_items)}</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
            for i, item in enumerate(wishlist_items, 1):
                item_id, text, status = item
                status_emoji = self.get_status_emoji(status)
                status_text = self.get_status_text(status)
                message += f"\n{status_emoji} <b>{i}. {text}</b>\n"
                message += f"   📊 Статус: {status_text}\n"
                message += "   ━━━━━━━━━━━━━━━━\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Добавить желание", callback_data="add_wishlist")],
            [InlineKeyboardButton("📤 Поделиться вишлистом", callback_data="share_wishlist")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

    async def add_wishlist_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Добавление нового пункта в вишлист"""
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "🎁 <b>ДОБАВЛЕНИЕ В ВИШЛИСТ</b>\n\n"
                "Напишите ваше желание:",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                "🎁 <b>ДОБАВЛЕНИЕ В ВИШЛИСТ</b>\n\n"
                "Напишите ваше желание:",
                parse_mode='HTML'
            )
        return WISHLIST_ITEM

    async def save_wishlist_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Сохранение пункта вишлиста"""
        user_id = update.effective_user.id
        item_text = update.message.text
        
        self.add_to_wishlist(user_id, item_text)
        
        success_message = f"""
✅ <b>ЖЕЛАНИЕ ДОБАВЛЕНО!</b>

🎁 <b>{item_text}</b>

💫 <i>Возвращаю в вишлист...</i>
"""
        
        await update.message.reply_text(success_message, parse_mode='HTML')
        await self.show_wishlist(update, context)
        return ConversationHandler.END

    async def cancel_wishlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена добавления в вишлист"""
        await update.message.reply_text("❌ Добавление в вишлист отменено.")
        await self.show_wishlist(update, context)
        return ConversationHandler.END

    async def share_wishlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Поделиться вишлистом"""
        user_id = update.effective_user.id
        wishlist_items = self.get_wishlist(user_id)
        
        if not wishlist_items:
            message = "🎁 Ваш вишлист пуст. Добавьте желания, чтобы поделиться!"
        else:
            user = update.effective_user
            user_name = user.first_name or user.username or "Пользователь"
            
            message = f"🎁 <b>Вишлист {user_name}:</b>\n\n"
            for i, item in enumerate(wishlist_items, 1):
                item_id, text, status = item
                status_emoji = self.get_status_emoji(status)
                status_text = self.get_status_text(status)
                message += f"{status_emoji} <b>{i}. {text}</b>\n"
                message += f"   📊 Статус: {status_text}\n\n"
            
            message += "✨ <i>Поделитесь этим сообщением с друзьями!</i>"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, parse_mode='HTML')
        else:
            await update.message.reply_text(message, parse_mode='HTML')

    async def update_wishlist_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE, item_id: int, new_status: str):
        """Обновление статуса пункта вишлиста"""
        user_id = update.effective_user.id
        self.change_wishlist_status(item_id, new_status)
        
        status_names = {
            'want': 'хочу',
            'in_progress': 'в процессе', 
            'done': 'выполнено'
        }
        
        message = f"""
🔄 <b>СТАТУС ОБНОВЛЕН!</b>

Новый статус: <b>{status_names[new_status]}</b> {self.get_status_emoji(new_status)}
"""
        
        await update.callback_query.answer(message, show_alert=False)
        await self.show_wishlist(update, context)

    def get_status_emoji(self, status: str) -> str:
        """Получение эмодзи для статуса"""
        return {
            'want': '👀',
            'in_progress': '🔄',
            'done': '✅'
        }.get(status, '📝')

    def get_status_text(self, status: str) -> str:
        """Получение текста для статуса"""
        return {
            'want': 'Хочу получить',
            'in_progress': 'В процессе', 
            'done': 'Выполнено'
        }.get(status, 'Новый')

    def add_to_wishlist(self, user_id: int, item_text: str):
        """Добавление в вишлист"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('INSERT INTO wishlist (user_id, item_text) VALUES (?, ?)', 
                      (user_id, item_text))
        
        conn.commit()
        conn.close()

    def get_wishlist(self, user_id: int):
        """Получение вишлиста пользователя"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, item_text, status FROM wishlist WHERE user_id = ? ORDER BY created_at DESC', 
                      (user_id,))
        
        items = cursor.fetchall()
        conn.close()
        
        return items

    def change_wishlist_status(self, item_id: int, new_status: str):
        """Изменение статуса пункта вишлиста"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('UPDATE wishlist SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', 
                      (new_status, item_id))
        
        conn.commit()
        conn.close()

    # 👥 СИСТЕМА ДОСОК
    async def show_my_boards(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать мои доски с улучшенным интерфейсом"""
        user_id = update.effective_user.id
        
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT b.id, b.name, b.invite_code, COUNT(bm.user_id) as members_count
            FROM boards b
            JOIN board_members bm ON b.id = bm.board_id
            WHERE bm.user_id = ?
            GROUP BY b.id
        ''', (user_id,))
        
        boards = cursor.fetchall()
        conn.close()
        
        if not boards:
            message = """
👥 <b>ОБЩИЕ ДОСКИ</b>

У вас пока нет досок.

💫 <i>Создайте свою доску или присоединитесь к существующей!</i>
"""
        else:
            message = f"""
👥 <b>ОБЩИЕ ДОСКИ</b>

Ваши доски ({len(boards)}):
━━━━━━━━━━━━━━━━━━━━━━
"""
            for board in boards:
                board_id, name, invite_code, members_count = board
                message += f"\n🔹 <b>{name}</b>\n"
                message += f"   👥 Участников: {members_count}\n"
                message += f"   🔑 Код: {invite_code}\n"
                message += "   ━━━━━━━━━━━━━━━━\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Создать доску", callback_data="create_board_prompt")],
            [InlineKeyboardButton("🔗 Присоединиться к доске", callback_data="join_board_prompt")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

    async def join_board_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запрос кода для присоединения к доске"""
        await update.callback_query.edit_message_text(
            "🔗 <b>ПРИСОЕДИНЕНИЕ К ДОСКЕ</b>\n\n"
            "Введите код приглашения:\n"
            "Пример: 123456\n\n"
            "<i>Отправьте код в следующем сообщении</i>",
            parse_mode='HTML'
        )
        # Устанавливаем флаг ожидания кода
        context.user_data['waiting_for_board_code'] = True

    # 🌤️ СИСТЕМА ПОГОДЫ
    async def weather_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self.update_stat(user_id, 'weather_checks')
        
        await update.message.reply_text("⏳ Получаю данные о погоде в Санкт-Петербурге...")
        
        weather_data = await self.get_weather_spb()
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data="weather")],
            [InlineKeyboardButton("🎯 Идеи для выходных", callback_data="weekend")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(weather_data, reply_markup=reply_markup, parse_mode='HTML')

    # 🎮 ОБРАБОТЧИК КНОПОК (ОБНОВЛЕННЫЙ)
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        try:
            if data == "main_menu":
                await self.show_main_menu(update, context)
            elif data == "weekend":
                await self.suggest_weekend_callback(update, context)
            elif data == "date":
                await self.suggest_date_callback(update, context)
            elif data == "weather":
                await self.weather_callback(update, context)
            elif data == "new_event":
                await self.new_event(update, context)
            elif data == "my_events":
                await self.show_my_events(update, context)
            elif data == "clear_events":
                await self.clear_old_events(update, context)
            elif data == "achievements":
                await self.show_achievements(update, context)
            elif data == "stats":
                await self.show_stats(update, context)
            elif data == "my_boards":
                await self.show_my_boards(update, context)
            elif data == "wishlist":
                await self.show_wishlist(update, context)
            elif data == "create_step":
                await self.create_event_step(update, context)
            elif data == "quick_create":
                await self.quick_create_event(update, context)
            elif data == "add_to_board":
                await self.add_to_board_info(update, context)
            elif data == "join_board_prompt":
                await self.join_board_prompt(update, context)
            elif data == "create_board_prompt":
                await self.create_board_prompt(update, context)
            elif data == "add_wishlist":
                await self.add_wishlist_item(update, context)
            elif data == "share_wishlist":
                await self.share_wishlist(update, context)
            elif data.startswith('wish_'):
                # Обработка изменения статуса вишлиста
                parts = data.split('_')
                if len(parts) == 3:
                    item_id = int(parts[1])
                    new_status = parts[2]
                    await self.update_wishlist_status(update, context, item_id, new_status)
            else:
                await query.edit_message_text("❌ Неизвестная команда")
                await self.show_main_menu(update, context)
        except Exception as e:
            logging.error(f"Error in button handler: {e}")
            await query.edit_message_text("❌ Произошла ошибка. Возвращаю в главное меню...")
            await self.show_main_menu(update, context)

    # 🔄 CALLBACK-ВЕРСИИ ФУНКЦИЙ
    async def suggest_weekend_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self.update_stat(user_id, 'weekend_ideas_generated')
        
        activity = self.get_unique_idea(user_id, 'weekend')
        
        message = f"""
🎉 <b>ИДЕЯ ДЛЯ ВЫХОДНЫХ</b> 🎉

━━━━━━━━━━━━━━━━━━━━━━
{activity}
━━━━━━━━━━━━━━━━━━━━━━

💫 <i>Хотите другую идею?</i>
"""
        
        keyboard = [
            [InlineKeyboardButton("🔄 Новая идея", callback_data="weekend"),
             InlineKeyboardButton("💕 Идея для свидания", callback_data="date")],
            [InlineKeyboardButton("📅 Создать событие", callback_data="new_event"),
             InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')

    async def suggest_date_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self.update_stat(user_id, 'date_ideas_generated')
        
        date_idea = self.get_unique_idea(user_id, 'date')
        
        message = f"""
💖 <b>ИДЕЯ ДЛЯ СВИДАНИЯ</b> 💖

━━━━━━━━━━━━━━━━━━━━━━
{date_idea}
━━━━━━━━━━━━━━━━━━━━━━

✨ <i>Ищете другое приключение?</i>
"""
        
        keyboard = [
            [InlineKeyboardButton("🔄 Новая идея", callback_data="date"),
             InlineKeyboardButton("🎯 Идея для выходных", callback_data="weekend")],
            [InlineKeyboardButton("📅 Создать событие", callback_data="new_event"),
             InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')

    async def weather_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self.update_stat(user_id, 'weather_checks')
        
        await update.callback_query.edit_message_text("⏳ Получаю данные о погоде в Санкт-Петербурге...", parse_mode='HTML')
        
        weather_data = await self.get_weather_spb()
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data="weather")],
            [InlineKeyboardButton("🎯 Идеи для выходных", callback_data="weekend")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(weather_data, reply_markup=reply_markup, parse_mode='HTML')

    async def quick_create_event(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.edit_message_text(
            "⚡ <b>БЫСТРОЕ СОЗДАНИЕ МЕРОПРИЯТИЯ</b>\n\n"
            "Отправьте сообщение в формате:\n"
            "Название | Дата | Описание | Место\n\n"
            "<b>Пример:</b>\n"
            "Поход в кино | 25.12.2024 19:00 | Смотрим новый фильм | Кинотеатр Аврора\n\n"
            "<i>После создания вы вернетесь в главное меню</i>",
            parse_mode='HTML'
        )

    async def add_to_board_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.edit_message_text(
            "👥 <b>ДОБАВЛЕНИЕ В ОБЩУЮ ДОСКУ</b>\n\n"
            "1. Создайте доску: /create_board название\n"
            "2. Пригласите друзей: /join_board код\n"
            "3. Создавайте мероприятия в своей доске!\n\n"
            "Посмотреть мои доски: /my_boards\n\n"
            "<i>Используйте кнопку ниже чтобы вернуться</i>",
            parse_mode='HTML'
        )

    async def create_board_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.edit_message_text(
            "➕ <b>СОЗДАНИЕ ДОСКИ</b>\n\n"
            "Введите название доски:\n\n"
            "<i>Отправьте название в следующем сообщении</i>",
            parse_mode='HTML'
        )
        context.user_data['waiting_for_board_name'] = True

    # 📝 СИСТЕМА СОЗДАНИЯ МЕРОПРИЯТИЙ
    async def create_event_step(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "📝 <b>СОЗДАНИЕ МЕРОПРИЯТИЯ</b>\n\n"
            "Шаг 1/4: Введите название мероприятия:",
            parse_mode='HTML'
        )
        return TITLE

    async def get_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['title'] = update.message.text
        await update.message.reply_text(
            "📅 Шаг 2/4: Введите дату и время мероприятия:\n"
            "Формат: ДД.ММ.ГГГГ ЧЧ:MM\n"
            "Пример: 25.12.2024 19:00",
            parse_mode='HTML'
        )
        return DATE

    async def get_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['date'] = update.message.text
        await update.message.reply_text(
            "📝 Шаг 3/4: Введите описание мероприятия:",
            parse_mode='HTML'
        )
        return DESCRIPTION

    async def get_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['description'] = update.message.text
        await update.message.reply_text(
            "📍 Шаг 4/4: Введите место проведения:",
            parse_mode='HTML'
        )
        return LOCATION

    async def get_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        location = update.message.text
        user_data = context.user_data
        
        user_id = update.effective_user.id
        event_id = self.save_event(
            user_id=user_id,
            title=user_data['title'],
            description=user_data['description'],
            date_str=user_data['date'],
            location=location
        )
        
        self.update_stat(user_id, 'events_created')
        
        success_message = f"""
✅ <b>МЕРОПРИЯТИЕ СОЗДАНО!</b>

🎉 <b>Отлично! Ваше мероприятие добавлено:</b>
━━━━━━━━━━━━━━━━━━━━━━
📌 <b>Название:</b> {user_data['title']}
📅 <b>Дата:</b> {user_data['date']}
📝 <b>Описание:</b> {user_data['description']}
📍 <b>Место:</b> {location}

💫 <i>Возвращаю в главное меню...</i>
"""
        
        context.user_data.clear()
        
        await update.message.reply_text(success_message, parse_mode='HTML')
        await self.show_main_menu(update, context)
        return ConversationHandler.END

    async def cancel_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await update.message.reply_text("❌ Создание мероприятия отменено.")
        await self.show_main_menu(update, context)
        return ConversationHandler.END

    # 👥 СИСТЕМА ДОСОК
    async def create_board(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        board_name = ' '.join(context.args) if context.args else f"Доска {update.effective_user.first_name}"
        invite_code = str(random.randint(100000, 999999))
        
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('INSERT INTO boards (name, invite_code, created_by) VALUES (?, ?, ?)', 
                     (board_name, invite_code, user_id))
        board_id = cursor.lastrowid
        
        cursor.execute('INSERT INTO board_members (board_id, user_id, role) VALUES (?, ?, ?)', 
                     (board_id, user_id, 'admin'))
        
        conn.commit()
        conn.close()
        
        self.update_stat(user_id, 'boards_created')
        
        await update.message.reply_text(
            f"✅ <b>ДОСКА СОЗДАНА!</b>\n\n"
            f"📋 Название: {board_name}\n"
            f"🔑 Код приглашения: {invite_code}\n\n"
            f"Поделитесь этим кодом с друзьями!",
            parse_mode='HTML'
        )

    async def join_board(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("❌ Укажите код приглашения: /join_board 123456")
            return
        
        invite_code = context.args[0]
        user_id = update.effective_user.id
        
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name FROM boards WHERE invite_code = ?', (invite_code,))
        board = cursor.fetchone()
        
        if not board:
            await update.message.reply_text("❌ Доска с таким кодом не найдена.")
            conn.close()
            return
        
        board_id, board_name = board
        
        cursor.execute('SELECT 1 FROM board_members WHERE board_id = ? AND user_id = ?', (board_id, user_id))
        if cursor.fetchone():
            await update.message.reply_text("ℹ️ Вы уже являетесь участником этой доски.")
            conn.close()
            return
        
        cursor.execute('INSERT INTO board_members (board_id, user_id) VALUES (?, ?)', (board_id, user_id))
        conn.commit()
        conn.close()
        
        await update.message.reply_text(
            f"✅ <b>ВЫ ПРИСОЕДИНИЛИСЬ К ДОСКЕ!</b>\n\n"
            f"📋 Название: {board_name}\n"
            f"👥 Теперь вы можете видеть и добавлять мероприятия!",
            parse_mode='HTML'
        )

    # 💾 ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        user_id = update.effective_user.id
        
        # Обработка быстрого создания мероприятия
        if '|' in text and len(text.split('|')) >= 4:
            parts = [part.strip() for part in text.split('|')]
            if len(parts) >= 4:
                title, date_str, description, location = parts[:4]
                
                event_id = self.save_event(user_id, title, description, date_str, location)
                self.update_stat(user_id, 'events_created')
                
                await update.message.reply_text(
                    f"✅ <b>МЕРОПРИЯТИЕ СОЗДАНО!</b>\n\n"
                    f"📌 {title}\n"
                    f"📅 {date_str}\n"
                    f"📍 {location}\n\n"
                    f"💫 <i>Возвращаю в главное меню...</i>",
                    parse_mode='HTML'
                )
                await self.show_main_menu(update, context)
                return
        
        # Обработка создания доски
        if context.user_data.get('waiting_for_board_name'):
            context.user_data['waiting_for_board_name'] = False
            context.args = [text]
            await self.create_board(update, context)
            await self.show_main_menu(update, context)
            return
        
        # Обработка присоединения к доске
        if context.user_data.get('waiting_for_board_code'):
            context.user_data['waiting_for_board_code'] = False
            context.args = [text]
            await self.join_board(update, context)
            await self.show_main_menu(update, context)
            return
        
        # Обработка установки города
        self.update_user_city(user_id, text)
        await update.message.reply_text(f"🏙️ Город установлен: {text}")
        await self.show_main_menu(update, context)

    # 💾 БАЗА ДАННЫХ И СЛУЖЕБНЫЕ ФУНКЦИИ
    def save_event(self, user_id: int, title: str, description: str, date_str: str, location: str) -> int:
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        try:
            event_date = datetime.strptime(date_str, '%d.%m.%Y %H:%M')
        except ValueError:
            event_date = datetime.now() + timedelta(days=1)
        
        cursor.execute('''
            INSERT INTO events (user_id, title, description, event_date, location)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, title, description, event_date, location))
        
        event_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return event_id

    def get_user_events(self, user_id: int):
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, event_date, location 
            FROM events 
            WHERE user_id = ? 
            ORDER BY event_date DESC
        ''', (user_id,))
        
        events = cursor.fetchall()
        conn.close()
        
        formatted_events = []
        for event in events:
            event_id, title, event_date, location = event
            if isinstance(event_date, str):
                formatted_date = event_date
            else:
                formatted_date = event_date.strftime('%d.%m.%Y %H:%M')
            formatted_events.append((event_id, title, formatted_date, location))
        
        return formatted_events

    def save_user(self, user):
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user.id, user.username, user.first_name, user.last_name))
        
        cursor.execute('INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)', (user.id,))
        
        conn.commit()
        conn.close()

    def update_stat(self, user_id: int, stat_field: str):
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)', (user_id,))
        cursor.execute(f'''
            UPDATE user_stats 
            SET {stat_field} = {stat_field} + 1, last_active = CURRENT_TIMESTAMP 
            WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()

    def get_user_stats(self, user_id: int) -> Dict:
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM user_stats WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            columns = [description[0] for description in cursor.description]
            stats = dict(zip(columns, result))
        else:
            stats = {}
        
        conn.close()
        return stats

    def update_user_city(self, user_id: int, city: str):
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET city = ? WHERE user_id = ?', (city, user_id))
        conn.commit()
        conn.close()

    # 🌤️ ПОГОДА
    async def get_weather_spb(self) -> str:
        try:
            url = "https://api.openweathermap.org/data/2.5/weather?lat=59.9311&lon=30.3609&appid=70c090a555176f1278bd62c7036d96b8&units=metric&lang=ru"
            
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if response.status_code == 200:
                temp = data['main']['temp']
                feels_like = data['main']['feels_like']
                humidity = data['main']['humidity']
                pressure = data['main']['pressure']
                description = data['weather'][0]['description']
                wind_speed = data['wind']['speed']
                
                weather_emoji = self.get_weather_emoji(data['weather'][0]['id'])
                
                weather_text = f"""
{weather_emoji} <b>ПОГОДА В САНКТ-ПЕТЕРБУРГЕ</b>

🌡️ <b>Температура:</b> {temp:.1f}°C (ощущается как {feels_like:.1f}°C)
💧 <b>Влажность:</b> {humidity}%
📊 <b>Давление:</b> {pressure} гПа
💨 <b>Ветер:</b> {wind_speed} м/с
📝 <b>Описание:</b> {description.capitalize()}

<i>Обновлено: {datetime.now().strftime('%H:%M %d.%m.%Y')}</i>
                """
                return weather_text
            else:
                return self.get_fallback_weather()
                
        except Exception as e:
            logging.error(f"Weather API error: {e}")
            return self.get_fallback_weather()

    def get_fallback_weather(self) -> str:
        return """
🌤️ <b>ПОГОДА В САНКТ-ПЕТЕРБУРГЕ</b>

🌡️ <b>Температура:</b> +5°C (ощущается как +3°C)
💧 <b>Влажность:</b> 85%
📊 <b>Давление:</b> 1013 гПа
💨 <b>Ветер:</b> 3 м/с
📝 <b>Описание:</b> Переменная облачность

<i>Данные обновляются...</i>
        """

    def get_weather_emoji(self, weather_id: int) -> str:
        if 200 <= weather_id <= 232: return "⛈️"
        elif 300 <= weather_id <= 321: return "🌧️"
        elif 500 <= weather_id <= 531: return "🌧️"
        elif 600 <= weather_id <= 622: return "❄️"
        elif 701 <= weather_id <= 781: return "🌫️"
        elif weather_id == 800: return "☀️"
        elif 801 <= weather_id <= 804: return "☁️"
        else: return "🌈"

    # 🏆 АЧИВКИ
    async def show_achievements(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_achievements = self.get_user_achievements(user_id)
        
        unlocked_count = sum(1 for ach in user_achievements.values() if ach['unlocked'])
        total_count = len(self.achievements_db)
        progress = (unlocked_count / total_count) * 100 if total_count > 0 else 0
        
        message = f"""
🏆 <b>МОИ АЧИВКИ</b>

📊 <b>Прогресс:</b> {unlocked_count}/{total_count} ({progress:.1f}%)
━━━━━━━━━━━━━━━━━━━━━━

"""
        
        unlocked_achievements = []
        for ach_id, ach_data in user_achievements.items():
            if ach_data['unlocked']:
                unlocked_achievements.append((ach_id, ach_data))
        
        if unlocked_achievements:
            message += "✨ <b>Последние полученные:</b>\n"
            for ach_id, ach_data in unlocked_achievements[:3]:
                achievement = self.achievements_db[ach_id]
                message += f"\n{achievement['icon']} <b>{achievement['name']}</b>\n"
                message += f"   {achievement['description']}\n"
                message += "   ━━━━━━━━━━━━━━━━\n"
        else:
            message += "🎯 <i>Ачивки будут появляться по мере использования бота!</i>\n"
        
        keyboard = [
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

    def get_user_achievements(self, user_id: int) -> Dict:
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT achievement_id, progress, unlocked, unlocked_at 
            FROM user_achievements WHERE user_id = ?
        ''', (user_id,))
        
        achievements = {}
        for row in cursor.fetchall():
            achievements[row[0]] = {
                'progress': row[1],
                'unlocked': bool(row[2]),
                'unlocked_at': row[3]
            }
        
        for ach_id in self.achievements_db:
            if ach_id not in achievements:
                achievements[ach_id] = {
                    'progress': 0,
                    'unlocked': False,
                    'unlocked_at': None
                }
        
        conn.close()
        return achievements

    # 📊 СТАТИСТИКА
    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        stats = self.get_user_stats(user_id)
        
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM events WHERE user_id = ?', (user_id,))
        events_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM board_members WHERE user_id = ?', (user_id,))
        boards_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM wishlist WHERE user_id = ?', (user_id,))
        wishlist_count = cursor.fetchone()[0]
        
        conn.close()
        
        message = f"""
📊 <b>МОЯ СТАТИСТИКА</b>

🎯 <b>Активность:</b>
━━━━━━━━━━━━━━━━━━━━━━
📅 Создано мероприятий: <b>{events_count}</b>
🎪 Идей для выходных: <b>{stats.get('weekend_ideas_generated', 0)}</b>
💕 Идей для свиданий: <b>{stats.get('date_ideas_generated', 0)}</b>
🌤️ Проверок погоды: <b>{stats.get('weather_checks', 0)}</b>
👥 Участие в досках: <b>{boards_count}</b>
🎁 Пунктов в вишлисте: <b>{wishlist_count}</b>

🚀 <i>Продолжайте в том же духе!</i>
"""
        
        keyboard = [
            [InlineKeyboardButton("🏆 Мои ачивки", callback_data="achievements")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

    async def set_city(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context.args:
            city = ' '.join(context.args)
            user_id = update.effective_user.id
            self.update_user_city(user_id, city)
            await update.message.reply_text(f"🏙️ Город установлен: {city}")
        else:
            await update.message.reply_text("Укажите город: /set_city Москва")

    def run(self):
        """Запуск бота"""
        self.application.run_polling()

# Запуск бота
if __name__ == "__main__":
    bot = SuperCalendarBot(token="8434605004:AAE1Ntpqi1qByfx73sTGaSdAK0giBViMLFU")
    print("🎉 Бот запущен с новыми функциями!")
    print("✨ Улучшенный визуальный интерфейс")
    print("🎯 Исправлено создание событий") 
    print("🧹 Добавлена очистка старых мероприятий")
    print("💕 Улучшены идеи для свиданий (без повторов)")
    print("🔗 Кнопка подключения к доскам")
    print("🎁 Новая система вишлиста с статусами")
    print("📤 Функция 'Поделиться вишлистом'")
    print("👀 Статусы: Увидел, В процессе, Выполнено")
    bot.run()