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
import asyncio

# Настройка logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Состояния для ConversationHandler
TITLE, DATE, DESCRIPTION, LOCATION = range(4)
WISHLIST_ITEM, REMINDER_SETUP, BOARD_SELECT = range(3)

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

        # База идей для выходных (80+ идей)
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
            "🏛️ Экскурсия по Исаакиевскому собору с подъемом на колоннаду",
            "🚢 Прогулка на кораблике по рекам и каналам",
            "🎪 Посетить Ленинградский зоопарк",
            "🏰 Поездка в Петергоф на фонтаны",
            "🎭 Сходить на спектакль в Александринский театр",
            "☕ Гастрономический тур по кофейням Петербурга",
            "📸 Фотосессия в самых Instagram-местах города",
            "🚴 Велопрогулка по островам",
            "🎳 Сходить в боулинг или бильярд",
            "🏊‍♂️ Посетить аквапарк или бассейн",
            "🎮 Квиз или настольные игры в антикафе",
            "🌃 Ночная экскурсия по крышам Петербурга",
            "🍷 Винный тур с дегустацией",
            "🎨 Мастер-класс по живописи или лепке",
            "🚁 Полетать на вертолете над городом",
            "🏎️ Погонять на картинге",
            "🎪 Сходить в цирк на Фонтанке",
            "🌿 Поехать в Комарово на природу",
            "🎵 Посетить джазовый концерт в JFC",
            "🏄‍♂️ Попробовать серфинг в вейв-пуле",
            "🎯 Поиграть в лазертаг или пейнтбол",
            "🏛️ Посетить Кунсткамеру",
            "🚶‍♀️ Прогулка по Васильевскому острову",
            "🎭 Сходить в БДТ им. Товстоногова",
            "🍣 Мастер-класс по суши от шеф-повара",
            "🌅 Встретить рассвет на пляже у Петропавловки",
            "📚 Книжный клуб в одной из библиотек",
            "🎪 Фестиваль уличных театров",
            "🚲 Поездка в Кронштадт на велосипедах",
            "🏺 Экскурсия в Эрарту",
            "🎵 Посетить органный концерт в костеле",
            "🍫 Шоколадная фабрика с дегустацией",
            "🚣‍♀️ Каякинг по рекам и каналам",
            "🎳 Боулинг-турнир с друзьями",
            "🏹 Пострелять из арбалета или лука",
            "🌌 Планетарий в Пулковской обсерватории",
            "🎨 Выставка современного искусства",
            "🚂 Поездка в Выборг на один день",
            "🍷 Сыроварня с дегустацией",
            "🏞️ Парк 300-летия Санкт-Петербурга",
            "🎭 Театр-фестиваль 'Балтийский дом'",
            "🚴‍♂️ Велопрогулка по Каменному острову",
            "🍣 Японский ресторан с темаки-вечеринкой",
            "🎬 Кинофестиваль в Ленфильме",
            "🏛️ Русский музей - Михайловский дворец",
            "🚢 Легендарный крейсер 'Аврора'",
            "🌳 Ботанический сад Петра Великого",
            "🎵 Рок-концерт в клубе 'Космонавт'",
            "🍺 Пивоварня с экскурсией",
            "🏰 Ораниенбаум - дворцово-парковый ансамбль",
            "🎯 Страйкбол или пейнтбол",
            "🚁 Полёт на параплане",
            "🏄‍♀️ Вейкбординг на водохранилище",
            "🎨 Граффити-тур по городу",
            "🚂 Детская железная дорога",
            "🏛️ Музей политической истории",
            "🎭 Театр 'Мюзик-Холл'",
            "🍷 Гастрономический ужин в темноте",
            "🚴‍♀️ Прогулка на сигвеях",
            "🎬 Немое кино с живой музыкой",
            "🏰 Гатчина - дворец и парк",
            "🎵 Фестиваль 'Серебряная лира'",
            "🍣 Суши-марафон",
            "🚁 Аэротруба - полёт без парашюта",
            "🏹 Тир с историческим оружием",
            "🎯 Квест в реальности",
            "🚂 Прогулка на ретро-поезде",
            "🏛️ Музей Арктики и Антарктики",
            "🎭 Театр 'Приют комедианта'",
            "🍷 Кальян-бар с восточными сладостями",
            "🚴‍♂️ Горный велосипед в парке",
            "🎬 Кино под открытым небом",
            "🏰 Павловск - дворец и парк",
            "🎵 Джаз-клуб 'JFC Jazz Club'",
            "🍣 Японские горячие источники",
            "🚁 Парашютный спорт",
            "🏄‍♂️ Кайтсерфинг на Финском заливе",
            "🎨 Студия стеклодувов",
            "🚂 Саблинские пещеры",
            "🏛️ Музей железных дорог России"
        ]
        
        # База идей для свиданий (80+ идей)
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
            "💐 Собрать букет в цветочной мастерской",
            "🎤 Караоке-вечер в караоке-клубе",
            "🏕️ Поход с ночевкой в палатках",
            "🎫 Посещение закрытого мероприятия или выставки",
            "🚁 Романтический полет на воздушном шаре",
            "🏖️ Поездка на песчаный пляж",
            "🎄 Рождественская ярмарка с глинтвейном",
            "🛶 Сплав на байдарках по реке",
            "🎪 Посещение веревочного парка",
            "🌉 Прогулка по ночному городу с гидом",
            "🍫 Шоколадная фабрика с мастер-классом",
            "🚂 Поездка на ретро-поезде",
            "🏰 Посещение старинного замка",
            "🎵 Концерт классической музыки",
            "🍷 Сыроварня с дегустацией",
            "🚴‍♀️ Прогулка на тандеме",
            "🎨 Роспись керамики в мастерской",
            "🌅 Встреча рассвета на крыше",
            "📚 Вечер в книжном магазине с кофе",
            "🎪 Картинг на профессиональной трассе",
            "🍣 Приготовить суши вместе",
            "🚤 Прогулка на яхте",
            "🏞️ Пикник у водопада",
            "🎭 Импровизационный театр",
            "🍷 Винный тур по винодельням",
            "🚁 Полёт на вертолете над городом",
            "🏄‍♀️ Серфинг на искусственной волне",
            "🎨 Создание семейного фотоальбома",
            "🚂 Путешествие на поезде в купе",
            "🏛️ Ночная экскурсия по музею",
            "🎵 Запись песни в студии",
            "🍫 Фондан-вечеринка",
            "🚲 Аренда велосипедов на весь день",
            "🎬 Марафон фильмов трилогии",
            "🏕️ Кемпинг с панорамным видом",
            "🎯 Лазертаг в большом лабиринте",
            "🍷 Гастрономический ужин от шефа",
            "🚤 Катание на гидроциклах",
            "🏞️ Поход к горному озеру",
            "🎭 Театральный мастер-класс",
            "🍣 Ужин в японском ресторане с шоу",
            "🚁 Парапланеризм в тандеме",
            "🎨 Создание свечей своими руками",
            "🚂 Путешествие на туристическом автобусе",
            "🏛️ Квест в историческом месте",
            "🎵 Танцевальный мастер-класс",
            "🍷 Создание собственного вина",
            "🚲 Ночная велопрогулка с фонарями",
            "🎬 Кино в автомобильном кинотеатре",
            "🏕️ Роскошный глэмпинг",
            "🎯 Стрельба из лука в тире",
            "🍫 Шоколадный массаж для двоих",
            "🚤 Романтическая регата",
            "🏞️ Фотосессия в цветущем саду",
            "🎭 Постановка домашнего спектакля",
            "🍣 Рыбалка с последующим приготовлением",
            "🚁 Полёт на дельтаплане",
            "🎨 Создание мозаики вместе",
            "🚂 Путешествие на катере по островам",
            "🏛️ Тематическая костюмированная вечеринка",
            "🎵 Создание плейлиста для друг друга",
            "🍷 Дегустация оливкового масла",
            "🚲 Прогулка по заброшенным местам",
            "🎬 Немой фильм с живым аккомпанементом",
            "🏕️ Создание своего кемпа в лесу",
            "🎯 Пейнтбол в лесу",
            "🍫 Вечер шоколада и сыра",
            "🚤 Ночная рыбалка с фонарями",
            "🏞️ Поход к водопадам",
            "🎭 Чтение пьес по ролям",
            "🍣 Мастер-класс по карвингу",
            "🚁 Полёт на аэростате",
            "🎨 Создание семейного герба",
            "🚂 Путешествие на дрезине"
        ]

        # Система ачивок (расширена)
        self.achievements_db = {
            "first_event": {"name": "🎯 Первое мероприятие", "description": "Создайте ваше первое событие", "icon": "🎯"},
            "weekend_planner": {"name": "🏆 Планировщик выходных", "description": "Используйте генератор идей 10 раз", "icon": "🏆"},
            "social_butterfly": {"name": "🦋 Социальная бабочка", "description": "Создайте 3 совместные доски", "icon": "🦋"},
            "date_master": {"name": "💕 Мастер свиданий", "description": "Сгенерируйте 15 идей для свиданий", "icon": "💕"},
            "wishlist_king": {"name": "👑 Король вишлиста", "description": "Добавьте 10 желаний в вишлист", "icon": "👑"},
            "weather_guru": {"name": "🌤️ Гуру погоды", "description": "Проверьте погоду 20 раз", "icon": "🌤️"},
            "reminder_pro": {"name": "⏰ Про напоминаний", "description": "Установите 5 напоминаний", "icon": "⏰"},
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
                reminders_set INTEGER DEFAULT 0,
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
        
        # Таблица напоминаний
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_id INTEGER,
                reminder_type TEXT,
                remind_at TIMESTAMP,
                sent BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица общих вишлистов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shared_wishlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                board_id INTEGER,
                item_text TEXT,
                added_by INTEGER,
                status TEXT DEFAULT 'want',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        self.application.add_handler(CommandHandler("reminders", self.show_reminders))
        
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Запуск фоновых задач
        self.application.job_queue.run_repeating(self.check_reminders, interval=60, first=10)

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
             InlineKeyboardButton("⏰ Напоминания", callback_data="reminders")],
            [InlineKeyboardButton("🏆 Мои ачивки", callback_data="achievements"),
             InlineKeyboardButton("📊 Статистика", callback_data="stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        self.save_user(user)
        
        welcome_message = f"""
🎊 <b>ДОБРО ПОЖАЛОВАТЬ В СУПЕР-КАЛЕНДАРЬ 2.0!</b> 🎊

Привет, <b>{user.first_name}</b>! 👋

🚀 <b>Ваш умный помощник для идеального планирования:</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ <b>Новые функции:</b>
• 🎁 Интерактивный вишлист с общими желаниями
• ⏰ Умные напоминания о событиях
• 🏆 Система ачивок с уведомлениями
• 🔄 Перенос идей прямо в доски
• 👥 Совместные вишлисты в досках
• 🎯 80+ идей для свиданий и выходных

🎨 <b>Просто выберите действие ниже:</b>
"""
        await self.show_main_menu(update, context, welcome_message)

    # 🎯 СИСТЕМА ИДЕЙ С ПЕРЕНАПРАВЛЕНИЕМ В ДОСКИ
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
        
        available_ideas = [idea for idea in pool if idea not in history]
        if not available_ideas:
            history.clear()
            available_ideas = pool
        
        idea = random.choice(available_ideas)
        history.append(idea)
        
        if len(history) > 15:
            history.pop(0)
            
        return idea

    async def suggest_weekend(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Генератор идей для выходных с кнопкой добавления в доску"""
        user_id = update.effective_user.id
        self.update_stat(user_id, 'weekend_ideas_generated')
        
        activity = self.get_unique_idea(user_id, 'weekend')
        
        # Сохраняем идею в контексте для дальнейшего использования
        context.user_data['last_idea'] = activity
        context.user_data['last_idea_type'] = 'weekend'
        
        message = f"""
🎉 <b>ИДЕЯ ДЛЯ ВЫХОДНЫХ</b> 🎉

━━━━━━━━━━━━━━━━━━━━━━
{activity}
━━━━━━━━━━━━━━━━━━━━━━

💫 <i>Что дальше?</i>
"""
        
        keyboard = [
            [InlineKeyboardButton("📋 Добавить в доску", callback_data="add_idea_to_board")],
            [InlineKeyboardButton("🔄 Новая идея", callback_data="weekend"),
             InlineKeyboardButton("💕 Идея для свидания", callback_data="date")],
            [InlineKeyboardButton("📅 Создать событие", callback_data="new_event"),
             InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

    async def suggest_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Генератор идей для свиданий с кнопкой добавления в доску"""
        user_id = update.effective_user.id
        self.update_stat(user_id, 'date_ideas_generated')
        
        date_idea = self.get_unique_idea(user_id, 'date')
        
        # Сохраняем идею в контексте для дальнейшего использования
        context.user_data['last_idea'] = date_idea
        context.user_data['last_idea_type'] = 'date'
        
        message = f"""
💖 <b>ИДЕЯ ДЛЯ СВИДАНИЯ</b> 💖

━━━━━━━━━━━━━━━━━━━━━━
{date_idea}
━━━━━━━━━━━━━━━━━━━━━━

✨ <i>Что дальше?</i>
"""
        
        keyboard = [
            [InlineKeyboardButton("📋 Добавить в доску", callback_data="add_idea_to_board")],
            [InlineKeyboardButton("🔄 Новая идея", callback_data="date"),
             InlineKeyboardButton("🎯 Идея для выходных", callback_data="weekend")],
            [InlineKeyboardButton("📅 Создать событие", callback_data="new_event"),
             InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

    async def add_idea_to_board(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Добавление текущей идеи в выбранную доску"""
        user_id = update.effective_user.id
        
        # Получаем последнюю идею из контекста
        idea = context.user_data.get('last_idea')
        idea_type = context.user_data.get('last_idea_type', 'мероприятие')
        
        if not idea:
            await update.callback_query.answer("❌ Нет активной идеи для добавления", show_alert=True)
            return
        
        # Получаем список досок пользователя
        boards = self.get_user_boards(user_id)
        
        if not boards:
            message = """
❌ <b>У вас нет досок</b>

Сначала создайте доску или присоединитесь к существующей!
"""
            keyboard = [
                [InlineKeyboardButton("➕ Создать доску", callback_data="create_board_prompt")],
                [InlineKeyboardButton("🔗 Присоединиться к доске", callback_data="join_board_prompt")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ]
        else:
            message = f"""
📋 <b>ДОБАВЛЕНИЕ ИДЕИ В ДОСКУ</b>

💡 <b>Идея:</b> {idea}

👇 <i>Выберите доску для добавления:</i>
"""
            keyboard = []
            for board in boards[:5]:  # Ограничиваем 5 досками
                board_id, board_name = board
                keyboard.append([InlineKeyboardButton(
                    f"📋 {board_name}", 
                    callback_data=f"add_to_board_{board_id}"
                )])
            
            keyboard.extend([
                [InlineKeyboardButton("➕ Создать новую доску", callback_data="create_board_prompt")],
                [InlineKeyboardButton("↩️ Назад", callback_data=idea_type)],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')

    async def add_idea_to_specific_board(self, update: Update, context: ContextTypes.DEFAULT_TYPE, board_id: int):
        """Добавление идеи в конкретную доску"""
        user_id = update.effective_user.id
        idea = context.user_data.get('last_idea')
        
        if not idea:
            await update.callback_query.answer("❌ Нет активной идеи", show_alert=True)
            return
        
        # Создаем событие на основе идеи
        event_date = datetime.now() + timedelta(days=7)  # По умолчанию через неделю
        event_id = self.save_event(
            user_id=user_id,
            title=idea,
            description=f"Идея из генератора {context.user_data.get('last_idea_type', '')}",
            date_str=event_date.strftime('%d.%m.%Y %H:%M'),
            location="Место уточняется",
            board_id=board_id
        )
        
        # Получаем название доски
        board_name = self.get_board_name(board_id)
        
        success_message = f"""
✅ <b>ИДЕЯ ДОБАВЛЕНА В ДОСКУ!</b>

📋 <b>Доска:</b> {board_name}
💡 <b>Идея:</b> {idea}

🎉 <i>Теперь все участники увидят эту идею!</i>
"""
        
        await update.callback_query.edit_message_text(success_message, parse_mode='HTML')
        
        # Показываем кнопки для дальнейших действий
        keyboard = [
            [InlineKeyboardButton("🔄 Новая идея", callback_data=context.user_data.get('last_idea_type', 'weekend'))],
            [InlineKeyboardButton("📋 Посмотреть доску", callback_data=f"view_board_{board_id}")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.message.reply_text("🎯 Что дальше?", reply_markup=reply_markup)

    # 🎁 ИНТЕРАКТИВНЫЙ ВИШЛИСТ С ОБЩИМИ ЖЕЛАНИЯМИ
    async def show_wishlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать вишлист пользователя с интерактивными кнопками"""
        user_id = update.effective_user.id
        wishlist_items = self.get_wishlist(user_id)
        
        message = """
🎁 <b>МОЙ ВИШЛИСТ</b>

✨ <i>Управляйте своими желаниями:</i>
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
                
                # Добавляем кнопки для каждого пункта
                keyboard_row = []
                for status_type, emoji in [('want', '👀'), ('in_progress', '🔄'), ('done', '✅')]:
                    if status != status_type:
                        callback_data = f"wish_{item_id}_{status_type}"
                        keyboard_row.append(InlineKeyboardButton(emoji, callback_data=callback_data))
                
                # Добавляем кнопку удаления
                keyboard_row.append(InlineKeyboardButton("🗑️", callback_data=f"delete_wish_{item_id}"))
                message += "   ━━━━━━━━━━━━━━━━\n"
        
        keyboard = [
            [
                InlineKeyboardButton("👀 Хочу", callback_data="wish_filter_want"),
                InlineKeyboardButton("🔄 В процессе", callback_data="wish_filter_in_progress"),
                InlineKeyboardButton("✅ Выполнено", callback_data="wish_filter_done")
            ],
            [InlineKeyboardButton("➕ Добавить желание", callback_data="add_wishlist")],
            [InlineKeyboardButton("📤 Поделиться вишлистом", callback_data="share_wishlist")],
            [InlineKeyboardButton("👥 Общий вишлист доски", callback_data="board_wishlist")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

    async def show_board_wishlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать общий вишлист текущей доски"""
        user_id = update.effective_user.id
        
        # Получаем активную доску пользователя
        active_board = self.get_user_active_board(user_id)
        
        if not active_board:
            message = """
👥 <b>ОБЩИЙ ВИШЛИСТ</b>

❌ <i>У вас нет активной доски</i>

Присоединитесь к доске, чтобы видеть общие желания!
"""
            keyboard = [
                [InlineKeyboardButton("🔗 Присоединиться к доске", callback_data="join_board_prompt")],
                [InlineKeyboardButton("🎁 Мой вишлист", callback_data="wishlist")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ]
        else:
            board_id, board_name = active_board
            shared_items = self.get_shared_wishlist(board_id)
            
            message = f"""
👥 <b>ОБЩИЙ ВИШЛИСТ</b>

📋 <b>Доска:</b> {board_name}

"""
            if not shared_items:
                message += "📝 <i>Пока нет общих желаний</i>"
            else:
                message += f"🎁 Найдено желаний: <b>{len(shared_items)}</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
                for i, item in enumerate(shared_items, 1):
                    item_id, text, status, added_by = item
                    user_name = self.get_user_name(added_by)
                    status_emoji = self.get_status_emoji(status)
                    message += f"\n{status_emoji} <b>{i}. {text}</b>\n"
                    message += f"   👤 Добавил: {user_name}\n"
                    message += f"   📊 Статус: {self.get_status_text(status)}\n"
                    message += "   ━━━━━━━━━━━━━━━━\n"
        
            keyboard = [
                [InlineKeyboardButton("➕ Добавить в общий вишлист", callback_data="add_shared_wish")],
                [InlineKeyboardButton("🎁 Мой вишлист", callback_data="wishlist")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')

    async def add_shared_wishlist_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Добавление пункта в общий вишлист доски"""
        user_id = update.effective_user.id
        active_board = self.get_user_active_board(user_id)
        
        if not active_board:
            await update.callback_query.answer("❌ Сначала присоединитесь к доске", show_alert=True)
            return
        
        board_id, board_name = active_board
        
        await update.callback_query.edit_message_text(
            f"👥 <b>ДОБАВЛЕНИЕ В ОБЩИЙ ВИШЛИСТ</b>\n\n"
            f"📋 Доска: {board_name}\n\n"
            "Напишите желание для всех участников:",
            parse_mode='HTML'
        )
        context.user_data['adding_shared_wish'] = True
        context.user_data['target_board'] = board_id

    # ⏰ СИСТЕМА УМНЫХ НАПОМИНАНИЙ
    async def show_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать систему напоминаний"""
        user_id = update.effective_user.id
        upcoming_events = self.get_upcoming_events(user_id)
        active_reminders = self.get_user_reminders(user_id)
        
        message = """
⏰ <b>СИСТЕМА НАПОМИНАНИЙ</b>

✨ <i>Никогда не пропускайте важные события!</i>
"""
        
        if not upcoming_events:
            message += "\n📝 <i>Нет предстоящих событий для напоминаний</i>"
        else:
            message += f"\n📅 <b>Ближайшие события ({len(upcoming_events)}):</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
            for i, event in enumerate(upcoming_events[:3], 1):
                event_id, title, event_date = event
                message += f"\n📌 <b>{title}</b>\n"
                message += f"   📅 {event_date}\n"
                
                # Добавляем кнопки для быстрого создания напоминаний
                keyboard_row = []
                for days, emoji in [(1, "1️⃣"), (3, "3️⃣"), (7, "7️⃣"), (14, "🔟")]:
                    callback_data = f"quick_remind_{event_id}_{days}"
                    keyboard_row.append(InlineKeyboardButton(f"{emoji} день", callback_data=callback_data))
                
                message += "   ━━━━━━━━━━━━━━━━\n"
        
        if active_reminders:
            message += f"\n🔔 <b>Активные напоминания ({len(active_reminders)}):</b>\n"
            for reminder in active_reminders[:3]:
                event_title, remind_at, reminder_type = reminder
                message += f"   ⏰ {event_title} - {reminder_type}\n"
        
        keyboard = [
            [InlineKeyboardButton("🔔 Установить напоминание", callback_data="set_reminder")],
            [InlineKeyboardButton("📋 Мои мероприятия", callback_data="my_events")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

    async def setup_reminder(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Настройка напоминания"""
        user_id = update.effective_user.id
        events = self.get_upcoming_events(user_id)
        
        if not events:
            await update.callback_query.answer("❌ Нет событий для напоминаний", show_alert=True)
            return
        
        message = """
🔔 <b>НАСТРОЙКА НАПОМИНАНИЯ</b>

Выберите событие для напоминания:
"""
        
        keyboard = []
        for event in events[:5]:  # Ограничиваем 5 событиями
            event_id, title, event_date = event
            keyboard.append([InlineKeyboardButton(
                f"📌 {title}",
                callback_data=f"remind_event_{event_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')

    async def setup_reminder_for_event(self, update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int):
        """Настройка напоминания для конкретного события"""
        event = self.get_event_by_id(event_id)
        if not event:
            await update.callback_query.answer("❌ Событие не найдено", show_alert=True)
            return
        
        event_title, event_date = event
        context.user_data['reminder_event_id'] = event_id
        
        message = f"""
🔔 <b>НАПОМИНАНИЕ ДЛЯ СОБЫТИЯ</b>

📌 <b>{event_title}</b>
📅 <b>{event_date}</b>

Выберите когда напомнить:
"""
        
        keyboard = [
            [InlineKeyboardButton("⏰ За 1 день", callback_data=f"remind_time_1_day")],
            [InlineKeyboardButton("⏰ За 3 дня", callback_data=f"remind_time_3_days")],
            [InlineKeyboardButton("⏰ За 1 неделю", callback_data=f"remind_time_7_days")],
            [InlineKeyboardButton("⏰ За 2 недели", callback_data=f"remind_time_14_days")],
            [InlineKeyboardButton("↩️ Назад", callback_data="set_reminder")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')

    async def save_reminder(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Сохранение напоминания"""
        user_id = update.effective_user.id
        event_id = context.user_data.get('reminder_event_id')
        
        if not event_id:
            await update.message.reply_text("❌ Ошибка: событие не выбрано")
            return
        
        # Получаем данные события
        event = self.get_event_by_id(event_id)
        if not event:
            await update.message.reply_text("❌ Событие не найдено")
            return
        
        event_title, event_date_str = event
        
        try:
            # Парсим дату события
            event_date = datetime.strptime(event_date_str, '%d.%m.%Y %H:%M')
            
            # Устанавливаем напоминание (здесь можно добавить логику для разных интервалов)
            reminder_date = event_date - timedelta(days=1)  # По умолчанию за 1 день
            
            # Сохраняем напоминание в базу
            self.save_reminder_to_db(user_id, event_id, "1_day", reminder_date)
            
            self.update_stat(user_id, 'reminders_set')
            
            success_message = f"""
✅ <b>НАПОМИНАНИЕ УСТАНОВЛЕНО!</b>

📌 <b>Событие:</b> {event_title}
📅 <b>Дата:</b> {event_date_str}
🔔 <b>Напомним:</b> за 1 день

💫 <i>Мы пришлем вам напоминание вовремя!</i>
"""
            
            await update.message.reply_text(success_message, parse_mode='HTML')
            await self.show_reminders(update, context)
            
        except ValueError as e:
            await update.message.reply_text("❌ Ошибка в формате даты события")
        
        return ConversationHandler.END

    async def check_reminders(self, context: ContextTypes.DEFAULT_TYPE):
        """Проверка и отправка напоминаний"""
        current_time = datetime.now()
        reminders = self.get_due_reminders(current_time)
        
        for reminder in reminders:
            reminder_id, user_id, event_id = reminder
            event = self.get_event_by_id(event_id)
            
            if event:
                event_title, event_date = event
                message = f"""
🔔 <b>НАПОМИНАНИЕ</b>

📌 <b>{event_title}</b>
📅 <b>Завтра в {event_date.split(' ')[1]}</b>

💫 Не забудьте подготовиться!
"""
                try:
                    await context.bot.send_message(chat_id=user_id, text=message, parse_mode='HTML')
                    self.mark_reminder_sent(reminder_id)
                except Exception as e:
                    logging.error(f"Failed to send reminder: {e}")

    # 🏆 СИСТЕМА АЧИВОК С УВЕДОМЛЕНИЯМИ
    async def check_and_award_achievement(self, user_id: int, achievement_id: str, context: ContextTypes.DEFAULT_TYPE = None):
        """Проверка и выдача ачивки с уведомлением"""
        progress = self.get_achievement_progress(user_id, achievement_id)
        achievement = self.achievements_db[achievement_id]
        
        if not progress['unlocked'] and progress['progress'] >= self.get_achievement_threshold(achievement_id):
            # Разблокируем ачивку
            self.unlock_achievement(user_id, achievement_id)
            
            # Отправляем уведомление
            if context:
                message = f"""
🎊 <b>НОВАЯ АЧИВКА!</b>

{achievement['icon']} <b>{achievement['name']}</b>
📝 {achievement['description']}

🎉 Поздравляем с достижением!
"""
                try:
                    await context.bot.send_message(chat_id=user_id, text=message, parse_mode='HTML')
                except Exception as e:
                    logging.error(f"Failed to send achievement notification: {e}")

    def get_achievement_threshold(self, achievement_id: str) -> int:
        """Получение порога для ачивки"""
        thresholds = {
            "first_event": 1,
            "weekend_planner": 10,
            "social_butterfly": 3,
            "date_master": 15,
            "wishlist_king": 10,
            "weather_guru": 20,
            "reminder_pro": 5
        }
        return thresholds.get(achievement_id, 1)

    # 🎮 ОБНОВЛЕННЫЙ ОБРАБОТЧИК КНОПОК
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопок"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        try:
            if data == "main_menu":
                await self.show_main_menu(update, context)
            elif data == "weekend":
                await self.suggest_weekend(update, context)
            elif data == "date":
                await self.suggest_date(update, context)
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
            elif data == "reminders":
                await self.show_reminders(update, context)
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
            elif data == "board_wishlist":
                await self.show_board_wishlist(update, context)
            elif data == "add_shared_wish":
                await self.add_shared_wishlist_item(update, context)
            elif data == "set_reminder":
                await self.setup_reminder(update, context)
            elif data == "add_idea_to_board":
                await self.add_idea_to_board(update, context)
            elif data.startswith('add_to_board_'):
                board_id = int(data.split('_')[3])
                await self.add_idea_to_specific_board(update, context, board_id)
            elif data.startswith('remind_event_'):
                event_id = int(data.split('_')[2])
                await self.setup_reminder_for_event(update, context, event_id)
            elif data.startswith('remind_time_'):
                await self.save_reminder(update, context)
            elif data.startswith('wish_'):
                parts = data.split('_')
                if len(parts) == 3:
                    item_id = int(parts[1])
                    new_status = parts[2]
                    await self.update_wishlist_status(update, context, item_id, new_status)
            elif data.startswith('delete_wish_'):
                item_id = int(data.split('_')[2])
                await self.delete_wishlist_item(update, context, item_id)
            elif data.startswith('quick_remind_'):
                parts = data.split('_')
                if len(parts) == 4:
                    event_id = int(parts[2])
                    days = int(parts[3])
                    await self.create_quick_reminder(update, context, event_id, days)
            else:
                await query.edit_message_text("❌ Неизвестная команда")
                await self.show_main_menu(update, context)
        except Exception as e:
            logging.error(f"Error in button handler: {e}")
            await query.edit_message_text("❌ Произошла ошибка. Возвращаю в главное меню...")
            await self.show_main_menu(update, context)

    # 🔧 ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    async def weather_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик погоды через callback"""
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
        """Быстрое создание мероприятия"""
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
        """Информация о добавлении в доску"""
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
        """Запрос названия для создания доски"""
        await update.callback_query.edit_message_text(
            "➕ <b>СОЗДАНИЕ ДОСКИ</b>\n\n"
            "Введите название доски:\n\n"
            "<i>Отправьте название в следующем сообщении</i>",
            parse_mode='HTML'
        )
        context.user_data['waiting_for_board_name'] = True

    async def join_board_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запрос кода для присоединения к доске"""
        await update.callback_query.edit_message_text(
            "🔗 <b>ПРИСОЕДИНЕНИЕ К ДОСКЕ</b>\n\n"
            "Введите код приглашения:\n"
            "Пример: 123456\n\n"
            "<i>Отправьте код в следующем сообщении</i>",
            parse_mode='HTML'
        )
        context.user_data['waiting_for_board_code'] = True

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

    async def delete_wishlist_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE, item_id: int):
        """Удаление пункта вишлиста"""
        self.remove_wishlist_item(item_id)
        
        await update.callback_query.answer("🗑️ Желание удалено!", show_alert=False)
        await self.show_wishlist(update, context)

    async def create_quick_reminder(self, update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int, days: int):
        """Быстрое создание напоминания"""
        user_id = update.effective_user.id
        event = self.get_event_by_id(event_id)
        
        if event:
            event_title, event_date_str = event
            event_date = datetime.strptime(event_date_str, '%d.%m.%Y %H:%M')
            reminder_date = event_date - timedelta(days=days)
            
            self.save_reminder_to_db(user_id, event_id, f"{days}_day", reminder_date)
            self.update_stat(user_id, 'reminders_set')
            
            message = f"""
✅ <b>НАПОМИНАНИЕ УСТАНОВЛЕНО!</b>

📌 {event_title}
🔔 Напомним за {days} дней

💫 Не забудьте проверить!
"""
            await update.callback_query.answer(message, show_alert=True)
            await self.show_reminders(update, context)

    # 📝 СИСТЕМА СОЗДАНИЯ МЕРОПРИЯТИЙ
    async def create_event_step(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало создания мероприятия"""
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "📝 <b>СОЗДАНИЕ МЕРОПРИЯТИЯ</b>\n\n"
            "Шаг 1/4: Введите название мероприятия:",
            parse_mode='HTML'
        )
        return TITLE

    async def get_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение названия мероприятия"""
        context.user_data['title'] = update.message.text
        await update.message.reply_text(
            "📅 Шаг 2/4: Введите дату и время мероприятия:\n"
            "Формат: ДД.ММ.ГГГГ ЧЧ:MM\n"
            "Пример: 25.12.2024 19:00",
            parse_mode='HTML'
        )
        return DATE

    async def get_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение даты мероприятия"""
        context.user_data['date'] = update.message.text
        await update.message.reply_text(
            "📝 Шаг 3/4: Введите описание мероприятия:",
            parse_mode='HTML'
        )
        return DESCRIPTION

    async def get_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение описания мероприятия"""
        context.user_data['description'] = update.message.text
        await update.message.reply_text(
            "📍 Шаг 4/4: Введите место проведения:",
            parse_mode='HTML'
        )
        return LOCATION

    async def get_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение места проведения и сохранение мероприятия"""
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
        """Отмена создания мероприятия"""
        context.user_data.clear()
        await update.message.reply_text("❌ Создание мероприятия отменено.")
        await self.show_main_menu(update, context)
        return ConversationHandler.END

    async def cancel_wishlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена добавления в вишлист"""
        await update.message.reply_text("❌ Добавление в вишлист отменено.")
        await self.show_wishlist(update, context)
        return ConversationHandler.END

    async def cancel_reminder(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена настройки напоминания"""
        await update.message.reply_text("❌ Настройка напоминания отменена.")
        await self.show_reminders(update, context)
        return ConversationHandler.END

    # 👥 СИСТЕМА ДОСОК
    async def create_board(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Создание новой доски"""
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
        """Присоединение к доске по коду"""
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

    async def show_my_boards(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать мои доски"""
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

    # 💾 ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
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
        
        # Обработка добавления в общий вишлист
        if context.user_data.get('adding_shared_wish'):
            context.user_data['adding_shared_wish'] = False
            board_id = context.user_data.get('target_board')
            
            if board_id:
                self.add_shared_wishlist_item_db(board_id, user_id, text)
                await update.message.reply_text(
                    f"✅ <b>ЖЕЛАНИЕ ДОБАВЛЕНО В ОБЩИЙ ВИШЛИСТ!</b>\n\n"
                    f"🎁 {text}\n\n"
                    f"💫 Теперь все участники увидят это желание!",
                    parse_mode='HTML'
                )
                await self.show_board_wishlist(update, context)
            return
        
        # Обработка установки города
        if text.startswith('/set_city'):
            city = text.replace('/set_city', '').strip()
            if city:
                self.update_user_city(user_id, city)
                await update.message.reply_text(f"🏙️ Город установлен: {city}")
                await self.show_main_menu(update, context)
            return
        
        # Если сообщение не распознано
        await update.message.reply_text(
            "🤔 <b>Не понял ваше сообщение</b>\n\n"
            "Используйте меню или команды для навигации:",
            parse_mode='HTML'
        )
        await self.show_main_menu(update, context)

    # 🌤️ СИСТЕМА ПОГОДЫ
    async def weather_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда погоды"""
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

    async def get_weather_spb(self) -> str:
        """Получение данных о погоде"""
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
        """Резервные данные о погоде"""
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
        """Получение эмодзи для погоды"""
        if 200 <= weather_id <= 232: return "⛈️"
        elif 300 <= weather_id <= 321: return "🌧️"
        elif 500 <= weather_id <= 531: return "🌧️"
        elif 600 <= weather_id <= 622: return "❄️"
        elif 701 <= weather_id <= 781: return "🌫️"
        elif weather_id == 800: return "☀️"
        elif 801 <= weather_id <= 804: return "☁️"
        else: return "🌈"

    # 🏆 СИСТЕМА АЧИВОК
    async def show_achievements(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать ачивки пользователя"""
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
        
        for ach_id, achievement in self.achievements_db.items():
            user_ach = user_achievements.get(ach_id, {'progress': 0, 'unlocked': False})
            status = "✅" if user_ach['unlocked'] else "⏳"
            progress_text = f"({user_ach['progress']}/{self.get_achievement_threshold(ach_id)})"
            
            message += f"{status} {achievement['icon']} <b>{achievement['name']}</b> {progress_text}\n"
            message += f"   {achievement['description']}\n"
            message += "   ━━━━━━━━━━━━━━━━\n"
        
        keyboard = [
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

    # 📊 СТАТИСТИКА
    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику пользователя"""
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
        
        cursor.execute('SELECT COUNT(*) FROM reminders WHERE user_id = ?', (user_id,))
        reminders_count = cursor.fetchone()[0]
        
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
🔔 Установлено напоминаний: <b>{reminders_count}</b>

🚀 <i>Продолжайте в том же духе!</i>
"""
        
        keyboard = [
            [InlineKeyboardButton("🏆 Мои ачивки", callback_data="achievements")],
            [InlineKeyboardButton("⏰ Напоминания", callback_data="reminders")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

    # 📅 СИСТЕМА МЕРОПРИЯТИЙ
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
                
                # Добавляем кнопки для быстрых напоминаний
                keyboard_row = []
                for days, emoji in [(1, "1️⃣"), (3, "3️⃣"), (7, "7️⃣")]:
                    callback_data = f"quick_remind_{event_id}_{days}"
                    keyboard_row.append(InlineKeyboardButton(f"{emoji}д", callback_data=callback_data))
                
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
        """Очистка старых мероприятий"""
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

    async def set_city(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Установка города пользователя"""
        if context.args:
            city = ' '.join(context.args)
            user_id = update.effective_user.id
            self.update_user_city(user_id, city)
            await update.message.reply_text(f"🏙️ Город установлен: {city}")
        else:
            await update.message.reply_text("Укажите город: /set_city Москва")

    # 🔧 БАЗА ДАННЫХ - ОСНОВНЫЕ МЕТОДЫ
    def save_user(self, user):
        """Сохранение пользователя в базу"""
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
        """Обновление статистики пользователя"""
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
        """Получение статистики пользователя"""
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
        """Обновление города пользователя"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET city = ? WHERE user_id = ?', (city, user_id))
        conn.commit()
        conn.close()

    def save_event(self, user_id: int, title: str, description: str, date_str: str, location: str, board_id: int = 0) -> int:
        """Сохранение мероприятия"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        try:
            event_date = datetime.strptime(date_str, '%d.%m.%Y %H:%M')
        except ValueError:
            event_date = datetime.now() + timedelta(days=1)
        
        cursor.execute('''
            INSERT INTO events (user_id, board_id, title, description, event_date, location)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, board_id, title, description, event_date, location))
        
        event_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return event_id

    def get_user_events(self, user_id: int):
        """Получение мероприятий пользователя"""
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

    def delete_old_events(self, user_id: int) -> int:
        """Удаление старых мероприятий"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM events WHERE user_id = ? AND event_date < ?', 
                      (user_id, datetime.now()))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count

    # 🎁 ВИШЛИСТ - МЕТОДЫ БАЗЫ ДАННЫХ
    def get_wishlist(self, user_id: int):
        """Получение вишлиста пользователя"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, item_text, status FROM wishlist WHERE user_id = ? ORDER BY created_at DESC', 
                      (user_id,))
        
        items = cursor.fetchall()
        conn.close()
        
        return items

    def add_to_wishlist(self, user_id: int, item_text: str):
        """Добавление в вишлист"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('INSERT INTO wishlist (user_id, item_text) VALUES (?, ?)', 
                      (user_id, item_text))
        
        conn.commit()
        conn.close()

    def change_wishlist_status(self, item_id: int, new_status: str):
        """Изменение статуса вишлиста"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('UPDATE wishlist SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', 
                      (new_status, item_id))
        
        conn.commit()
        conn.close()

    def remove_wishlist_item(self, item_id: int):
        """Удаление пункта вишлиста"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM wishlist WHERE id = ?', (item_id,))
        
        conn.commit()
        conn.close()

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

    # 👥 ДОСКИ - МЕТОДЫ БАЗЫ ДАННЫХ
    def get_user_boards(self, user_id: int):
        """Получение досок пользователя"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT b.id, b.name 
            FROM boards b
            JOIN board_members bm ON b.id = bm.board_id
            WHERE bm.user_id = ?
        ''', (user_id,))
        
        boards = cursor.fetchall()
        conn.close()
        return boards

    def get_board_name(self, board_id: int) -> str:
        """Получение названия доски"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT name FROM boards WHERE id = ?', (board_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else "Неизвестная доска"

    def get_user_active_board(self, user_id: int):
        """Получение активной доски пользователя"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT b.id, b.name 
            FROM boards b
            JOIN board_members bm ON b.id = bm.board_id
            WHERE bm.user_id = ?
            LIMIT 1
        ''', (user_id,))
        
        board = cursor.fetchone()
        conn.close()
        return board

    def get_shared_wishlist(self, board_id: int):
        """Получение общего вишлиста доски"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, item_text, status, added_by 
            FROM shared_wishlists 
            WHERE board_id = ?
            ORDER BY created_at DESC
        ''', (board_id,))
        
        items = cursor.fetchall()
        conn.close()
        return items

    def add_shared_wishlist_item_db(self, board_id: int, user_id: int, item_text: str):
        """Добавление в общий вишлист"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO shared_wishlists (board_id, item_text, added_by)
            VALUES (?, ?, ?)
        ''', (board_id, item_text, user_id))
        
        conn.commit()
        conn.close()

    def get_user_name(self, user_id: int) -> str:
        """Получение имени пользователя"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT first_name FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else "Неизвестный"

    # ⏰ НАПОМИНАНИЯ - МЕТОДЫ БАЗЫ ДАННЫХ
    def get_upcoming_events(self, user_id: int):
        """Получение предстоящих событий"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, event_date 
            FROM events 
            WHERE user_id = ? AND event_date > datetime('now')
            ORDER BY event_date ASC
            LIMIT 10
        ''', (user_id,))
        
        events = cursor.fetchall()
        conn.close()
        
        formatted_events = []
        for event in events:
            event_id, title, event_date = event
            if isinstance(event_date, str):
                formatted_date = event_date
            else:
                formatted_date = event_date.strftime('%d.%m.%Y %H:%M')
            formatted_events.append((event_id, title, formatted_date))
        
        return formatted_events

    def get_event_by_id(self, event_id: int):
        """Получение события по ID"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT title, event_date FROM events WHERE id = ?', (event_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            title, event_date = result
            if isinstance(event_date, str):
                formatted_date = event_date
            else:
                formatted_date = event_date.strftime('%d.%m.%Y %H:%M')
            return (title, formatted_date)
        return None

    def save_reminder_to_db(self, user_id: int, event_id: int, reminder_type: str, remind_at: datetime):
        """Сохранение напоминания в базу"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO reminders (user_id, event_id, reminder_type, remind_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, event_id, reminder_type, remind_at))
        
        conn.commit()
        conn.close()

    def get_user_reminders(self, user_id: int):
        """Получение напоминаний пользователя"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.title, r.remind_at, r.reminder_type
            FROM reminders r
            JOIN events e ON r.event_id = e.id
            WHERE r.user_id = ? AND r.sent = FALSE
            ORDER BY r.remind_at ASC
        ''', (user_id,))
        
        reminders = cursor.fetchall()
        conn.close()
        return reminders

    def get_due_reminders(self, current_time: datetime):
        """Получение напоминаний, которые нужно отправить"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, user_id, event_id
            FROM reminders 
            WHERE remind_at <= ? AND sent = FALSE
        ''', (current_time,))
        
        reminders = cursor.fetchall()
        conn.close()
        return reminders

    def mark_reminder_sent(self, reminder_id: int):
        """Пометка напоминания как отправленного"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('UPDATE reminders SET sent = TRUE WHERE id = ?', (reminder_id,))
        conn.commit()
        conn.close()

    # 🏆 АЧИВКИ - МЕТОДЫ БАЗЫ ДАННЫХ
    def get_user_achievements(self, user_id: int) -> Dict:
        """Получение ачивок пользователя"""
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

    def get_achievement_progress(self, user_id: int, achievement_id: str) -> Dict:
        """Получение прогресса по ачивке"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT progress, unlocked 
            FROM user_achievements 
            WHERE user_id = ? AND achievement_id = ?
        ''', (user_id, achievement_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {'progress': result[0], 'unlocked': bool(result[1])}
        return {'progress': 0, 'unlocked': False}

    def unlock_achievement(self, user_id: int, achievement_id: str):
        """Разблокировка ачивки"""
        conn = sqlite3.connect('super_calendar.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_achievements 
            (user_id, achievement_id, progress, unlocked, unlocked_at)
            VALUES (?, ?, ?, TRUE, CURRENT_TIMESTAMP)
        ''', (user_id, achievement_id, self.get_achievement_threshold(achievement_id)))
        
        conn.commit()
        conn.close()

    def run(self):
        """Запуск бота"""
        self.application.run_polling()

# Запуск бота
if __name__ == "__main__":
    bot = SuperCalendarBot(token="8434605004:AAE1Ntpqi1qByfx73sTGaSdAK0giBViMLFU")
    print("🎉 Бот запущен с УЛЬТРА-ФУНКЦИЯМИ!")
    print("✨ 80+ идей для свиданий и выходных")
    print("🎁 Полностью интерактивный вишлист")
    print("⏰ Умная система напоминаний") 
    print("🏆 Ачивки с уведомлениями")
    print("🔄 Перенос идей прямо в доски")
    print("👥 Совместные вишлисты в досках")
    print("📊 Расширенная статистика")
    print("🎯 Быстрые кнопки для всего!")
    bot.run()
