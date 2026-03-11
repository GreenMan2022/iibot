// Состояние чата
let messageCount = 0;
let isWaitingForResponse = false;
let lastRequestTime = 0;
const RATE_LIMIT_SECONDS = 25;

// Элементы DOM
const messagesArea = document.getElementById('messages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const typingIndicator = document.getElementById('typingIndicator');
const messageCountSpan = document.getElementById('messageCount');

// Авто resize текстового поля
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = (textarea.scrollHeight) + 'px';
}

// Добавление сообщения
function addMessage(text, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = isUser ? '👤' : '🤖';
    
    const content = document.createElement('div');
    content.className = 'content';
    
    const textDiv = document.createElement('div');
    textDiv.textContent = text;
    
    const timestamp = document.createElement('div');
    timestamp.className = 'timestamp';
    timestamp.textContent = new Date().toLocaleTimeString('ru-RU', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    content.appendChild(textDiv);
    content.appendChild(timestamp);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    messagesArea.appendChild(messageDiv);
    messagesArea.scrollTop = messagesArea.scrollHeight;
    
    if (!isUser) {
        messageCount++;
        messageCountSpan.textContent = messageCount;
    }
}

// Показать ошибку
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = `❌ ${message}`;
    messagesArea.appendChild(errorDiv);
    messagesArea.scrollTop = messagesArea.scrollHeight;
    
    setTimeout(() => errorDiv.remove(), 5000);
}

// Отправка сообщения
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message || isWaitingForResponse) return;

    // Проверка rate limit
    const now = Date.now();
    if (now - lastRequestTime < RATE_LIMIT_SECONDS * 1000) {
        const waitTime = Math.ceil((RATE_LIMIT_SECONDS * 1000 - (now - lastRequestTime)) / 1000);
        showError(`Подождите ${waitTime} сек. перед следующим запросом`);
        return;
    }

    // Добавляем сообщение пользователя
    addMessage(message, true);
    userInput.value = '';
    userInput.style.height = 'auto';
    
    // Блокируем ввод
    isWaitingForResponse = true;
    sendBtn.disabled = true;
    userInput.disabled = true;
    typingIndicator.style.display = 'flex';

    try {
        // Отправляем на бэкенд
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}`);
        }

        // Получаем ответ от AI
        let botReply = "Извините, не удалось получить ответ";
        if (data.response) {
            botReply = data.response;
        } else if (data.message) {
            botReply = data.message;
        } else if (typeof data === 'string') {
            botReply = data;
        }

        addMessage(botReply);
        lastRequestTime = Date.now();

    } catch (error) {
        console.error('Ошибка:', error);
        showError(error.message || 'Ошибка соединения');
    } finally {
        isWaitingForResponse = false;
        sendBtn.disabled = false;
        userInput.disabled = false;
        typingIndicator.style.display = 'none';
        userInput.focus();
    }
}

// Очистка чата
function clearChat() {
    messagesArea.innerHTML = `
        <div class="message bot">
            <div class="avatar">🤖</div>
            <div class="content">
                Чат очищен. Задайте новый вопрос!
                <div class="timestamp">${new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}</div>
            </div>
        </div>
    `;
    messageCount = 0;
    messageCountSpan.textContent = '0';
}

// Сохранение истории
function saveChat() {
    const messages = [];
    document.querySelectorAll('.message').forEach(msg => {
        const isUser = msg.classList.contains('user');
        const text = msg.querySelector('.content div:first-child')?.textContent || '';
        const time = msg.querySelector('.timestamp')?.textContent || '';
        messages.push({ text, isUser, time });
    });
    
    fetch('/api/history', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(messages)
    })
    .then(() => showError('✅ История сохранена'))
    .catch(() => showError('❌ Ошибка сохранения'));
}

// События
sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

document.getElementById('clearChatBtn').addEventListener('click', clearChat);
document.getElementById('saveChatBtn').addEventListener('click', saveChat);

// Приветственное сообщение
console.log('✅ Чат готов к работе на Flask!');
