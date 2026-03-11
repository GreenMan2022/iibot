import os
import logging
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла (для локальной разработки)
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)

# Проверка необходимых переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не установлен! Бот не будет работать.")
else:
    logger.info("BOT_TOKEN найден")

# Инициализация бота (если используется python-telegram-bot)
try:
    from telegram import Update, Bot
    from telegram.ext import Application, CommandHandler, ContextTypes
    
    # Создаем приложение бота
    bot_app = Application.builder().token(BOT_TOKEN).build()
    
    # Определяем обработчики команд
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Привет! Я бот. Используй /help для списка команд')
    
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Доступные команды:\n/start - Начать\n/help - Помощь')
    
    # Регистрируем обработчики
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("help", help_command))
    
    logger.info("Бот успешно инициализирован")
    
except ImportError:
    logger.warning("python-telegram-bot не установлен, функции бота недоступны")
    bot_app = None
except Exception as e:
    logger.error(f"Ошибка при инициализации бота: {e}")
    bot_app = None

# Функция для запуска бота в фоне
def run_bot():
    if bot_app:
        try:
            logger.info("Запуск бота...")
            bot_app.run_polling()
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")

# Запускаем бота в отдельном потоке при старте приложения
import threading
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()
logger.info("Поток бота запущен")

# Основные маршруты веб-приложения
@app.route('/')
def index():
    """Главная страница"""
    try:
        current_time = datetime.now()
        return render_template('index.html', now=current_time)
    except Exception as e:
        logger.error(f"Ошибка при загрузке главной страницы: {e}")
        return "Произошла ошибка при загрузке страницы", 500

@app.route('/health')
def health():
    """Эндпоинт для проверки здоровья приложения"""
    status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'bot_running': bot_app is not None
    }
    return jsonify(status)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Эндпоинт для вебхуков Telegram (если используете вебхуки вместо polling)"""
    if bot_app and request.is_json:
        try:
            update = Update.de_json(request.get_json(force=True), bot_app.bot)
            # Обработка update здесь
            return jsonify({'status': 'ok'})
        except Exception as e:
            logger.error(f"Ошибка при обработке вебхука: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    return jsonify({'status': 'no bot or invalid request'}), 400

@app.errorhandler(404)
def not_found(error):
    """Обработчик ошибки 404"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Обработчик ошибки 500"""
    logger.error(f"Внутренняя ошибка сервера: {error}")
    return render_template('500.html'), 500

# Для локального запуска
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
