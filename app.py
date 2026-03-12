import os
import logging
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, abort
from functools import wraps
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-12345')

# ============= ДЕКОРАТОРЫ И ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =============

def handle_api_errors(f):
    """Декоратор для обработки ошибок API"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except requests.exceptions.ConnectionError:
            logger.error("Ошибка подключения к API")
            return jsonify({'error': 'Нет подключения к API'}), 503
        except requests.exceptions.Timeout:
            logger.error("Таймаут API")
            return jsonify({'error': 'Превышено время ожидания API'}), 504
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return jsonify({'error': 'Неверный формат ответа от API'}), 502
        except Exception as e:
            logger.error(f"Неизвестная ошибка: {e}")
            return jsonify({'error': 'Внутренняя ошибка сервера'}), 500
    return decorated_function

def safe_json_parse(response_text):
    """Безопасный парсинг JSON с обработкой ошибок"""
    try:
        # Удаляем BOM если есть
        clean_text = response_text.replace('\ufeff', '')
        return json.loads(clean_text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        logger.debug(f"Problematic text: {response_text[:200]}")
        return None

# ============= МАРШРУТЫ ДЛЯ СТРАНИЦ =============

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html', now=datetime.now())

@app.route('/about')
def about():
    """Страница о нас"""
    return render_template('about.html')

@app.route('/api-demo')
def api_demo():
    """Страница для демонстрации работы с API"""
    return render_template('api_demo.html')

@app.route('/json-demo')
def json_demo():
    """Страница для демонстрации JSON парсинга"""
    return render_template('json_demo.html')

# ============= СОБСТВЕННЫЕ API ЭНДПОИНТЫ =============

@app.route('/api/data')
@handle_api_errors
def get_data():
    """Наш API endpoint возвращающий JSON"""
    data = {
        'status': 'success',
        'timestamp': datetime.now().isoformat(),
        'message': 'Данные успешно получены',
        'data': [
            {'id': 1, 'name': 'Элемент 1', 'value': 100},
            {'id': 2, 'name': 'Элемент 2', 'value': 200},
            {'id': 3, 'name': 'Элемент 3', 'value': 300}
        ]
    }
    return jsonify(data)

@app.route('/api/echo', methods=['POST'])
@handle_api_errors
def echo():
    """API эхо-сервер"""
    if not request.is_json:
        return jsonify({'error': 'Content-Type должен быть application/json'}), 400
    
    data = request.get_json()
    logger.info(f"Получены данные: {data}")
    
    response = {
        'status': 'success',
        'received': data,
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(response)

@app.route('/api/validate-json', methods=['POST'])
def validate_json():
    """Проверка валидности JSON"""
    try:
        data = request.get_data(as_text=True)
        
        # Пытаемся распарсить JSON
        parsed = safe_json_parse(data)
        
        if parsed is not None:
            return jsonify({
                'valid': True,
                'data': parsed,
                'message': 'JSON валиден'
            })
        else:
            return jsonify({
                'valid': False,
                'message': 'Невалидный JSON',
                'received': data[:200]
            }), 400
            
    except Exception as e:
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 500

# ============= ПРОКСИ ДЛЯ ВНЕШНИХ API =============

@app.route('/api/proxy/jsonplaceholder')
@handle_api_errors
def proxy_jsonplaceholder():
    """Прокси для JSONPlaceholder API (тестовое API)"""
    try:
        # Получаем параметры запроса
        resource = request.args.get('resource', 'posts')
        limit = request.args.get('limit', 5)
        
        # Делаем запрос к внешнему API
        url = f'https://jsonplaceholder.typicode.com/{resource}?_limit={limit}'
        logger.info(f"Запрос к внешнему API: {url}")
        
        response = requests.get(url, timeout=5)
        
        # Проверяем статус
        if response.status_code != 200:
            return jsonify({
                'error': f'Внешнее API вернуло статус {response.status_code}',
                'details': response.text[:200]
            }), response.status_code
        
        # Парсим JSON
        data = safe_json_parse(response.text)
        if data is None:
            return jsonify({'error': 'Не удалось распарсить ответ внешнего API'}), 502
        
        return jsonify({
            'status': 'success',
            'source': url,
            'data': data
        })
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса к внешнему API: {e}")
        return jsonify({'error': 'Ошибка при запросе к внешнему API'}), 502

@app.route('/api/proxy/random-user')
@handle_api_errors
def proxy_random_user():
    """Прокси для Random User API"""
    try:
        response = requests.get('https://randomuser.me/api/', timeout=5)
        
        if response.status_code != 200:
            return jsonify({'error': 'Ошибка получения данных'}), response.status_code
        
        data = safe_json_parse(response.text)
        if data is None:
            return jsonify({'error': 'Невалидный JSON от API'}), 502
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return jsonify({'error': str(e)}), 500

# ============= ОБРАБОТЧИКИ ОШИБОК =============

@app.errorhandler(404)
def not_found(error):
    """Страница 404"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'API endpoint не найден'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Страница 500"""
    logger.error(f"Внутренняя ошибка: {error}")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500
    return render_template('500.html'), 500

# ============= ЗАПУСК ПРИЛОЖЕНИЯ =============

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Запуск приложения на порту {port}, debug={debug}")
    app.run(host='0.0.0.0', port=port, debug=debug)
