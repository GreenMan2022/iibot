from flask import Flask, render_template, jsonify, request
import requests
import json

app = Flask(__name__)

# Конфигурация API
API_KEY = "apf_i6fhd1fenfma3zg2ceoaa5y5"
API_URL = "https://apifreellm.com/api/v1/chat"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Эндпоинт для AI чата"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({"error": "Пустое сообщение"}), 400
        
        # Отправляем запрос к API FreeLLM
        response = requests.post(
            API_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}"
            },
            json={
                "message": user_message
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                "error": f"API вернул ошибку: {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({"error": "Таймаут запроса к API"}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Ошибка подключения к API"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET', 'POST'])
def chat_history():
    """Сохранение и загрузка истории чата"""
    if request.method == 'POST':
        # Сохраняем историю
        data = request.json
        # Здесь можно сохранять в базу данных или файл
        print("Сохранена история чата:", data)
        return jsonify({"status": "success"})
    else:
        # Загружаем историю
        # Пока возвращаем пустую историю
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)
