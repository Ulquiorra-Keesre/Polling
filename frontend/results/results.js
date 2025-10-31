// Конфигурация API
const API_CONFIG = {
    BASE_URL: 'http://localhost:3000/api', // Замените на ваш URL сервера
    ENDPOINTS: {
        POLL_RESULTS: '/polls',
        AUTH: '/auth'
    }
};

// Функция для выполнения API запросов
async function apiRequest(endpoint, options = {}) {
    try {
        const url = `${API_CONFIG.BASE_URL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };

        // Добавляем токен авторизации, если есть
        const token = getAuthToken();
        if (token) {
            defaultOptions.headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Получение токена авторизации
function getAuthToken() {
    return localStorage.getItem('authToken');
}

// Загрузка результатов опроса с сервера
async function loadPollResults(pollId) {
    try {
        showLoading();
        
        const results = await apiRequest(`${API_CONFIG.ENDPOINTS.POLL_RESULTS}/${pollId}/results`);
        return results;
    } catch (error) {
        console.error('Error loading poll results:', error);
        throw new Error('Не удалось загрузить результаты опроса');
    }
}

// Загрузка информации об опросе
async function loadPollInfo(pollId) {
    try {
        const poll = await apiRequest(`${API_CONFIG.ENDPOINTS.POLL_RESULTS}/${pollId}`);
        return poll;
    } catch (error) {
        console.error('Error loading poll info:', error);
        throw new Error('Не удалось загрузить информацию об опросе');
    }
}

// Function to render results
function renderResults(pollData) {
    // Update poll info
    document.getElementById('resultsPollTitle').textContent = pollData.title;
    document.getElementById('resultsPollDescription').textContent = pollData.description;
    document.getElementById('resultsTotalVotes').textContent = `${pollData.totalVotes} голосов`;
    document.getElementById('pollEndDate').textContent = `Завершается: ${formatDate(pollData.endDate)}`;
    
    // Render results items
    const resultsItems = document.getElementById('resultsItems');
    resultsItems.innerHTML = '';
    
    if (!pollData.options || pollData.options.length === 0) {
        resultsItems.innerHTML = '<div class="no-results">Нет данных для отображения</div>';
        return;
    }
    
    pollData.options.forEach((option, index) => {
        const percentage = pollData.totalVotes > 0 
            ? Math.round((option.votes / pollData.totalVotes) * 100)
            : 0;
        
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item';
        resultItem.innerHTML = `
            <div class="result-header">
                <div class="result-option">
                    <div class="result-option-number">${index + 1}</div>
                    ${option.text}
                </div>
                <div class="result-stats">${percentage}% (${option.votes})</div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${percentage}%"></div>
            </div>
        `;
        resultsItems.appendChild(resultItem);
    });
}

// Format date function
function formatDate(dateString) {
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    };
    return new Date(dateString).toLocaleDateString('ru-RU', options);
}

// Update user info
function updateUserInfo() {
    const userData = getUserData();
    if (userData) {
        document.getElementById('userName').textContent = userData.name || `Студент ${userData.id}`;
        document.getElementById('userFaculty').textContent = userData.faculty || 'Факультет информатики';
        
        // Обновляем аватар с первой буквой имени
        const avatar = document.getElementById('userAvatar');
        if (avatar && userData.name) {
            avatar.textContent = userData.name.charAt(0).toUpperCase();
        }
    }
}

// Получение данных пользователя
function getUserData() {
    const userData = localStorage.getItem('userData');
    return userData ? JSON.parse(userData) : null;
}

// Logout functionality
function setupLogout() {
    document.getElementById('logoutBtn').addEventListener('click', function() {
        if (confirm('Вы уверены, что хотите выйти из системы?')) {
            // Очищаем localStorage
            localStorage.removeItem('authToken');
            localStorage.removeItem('userData');
            localStorage.removeItem('isAuthenticated');
            
            // Перенаправляем на страницу авторизации (в папку index)
            window.location.href = '../index/index.html';
        }
    });
}

// Back button functionality
function setupBackButton() {
    document.getElementById('backBtn').addEventListener('click', function(e) {
        e.preventDefault();
        window.location.href = '../dashboard/dashboard.html';
    });
}

// Helper function to get poll ID from URL
function getPollIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('pollId');
}

// Check authentication
function checkAuth() {
    const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
    const authToken = getAuthToken();
    
    if (!isAuthenticated || !authToken) {
        alert('Пожалуйста, авторизуйтесь');
        // Перенаправляем в папку index
        window.location.href = '../index/index.html';
        return false;
    }
    return true;
}

// Показать состояние загрузки
function showLoading() {
    const resultsItems = document.getElementById('resultsItems');
    resultsItems.innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Загрузка результатов...</p>
        </div>
    `;
}

// Показать ошибку
function showError(message) {
    const resultsItems = document.getElementById('resultsItems');
    resultsItems.innerHTML = `
        <div class="error-message">
            <i class="fas fa-exclamation-triangle"></i>
            <h3>Ошибка</h3>
            <p>${message}</p>
            <button class="retry-btn" onclick="location.reload()">
                <i class="fas fa-redo"></i>
                Попробовать снова
            </button>
        </div>
    `;
}

// Основная функция инициализации
async function initPage() {
    // Проверяем авторизацию
    if (!checkAuth()) return;
    
    // Настраиваем обработчики событий
    setupLogout();
    setupBackButton();
    
    // Обновляем информацию пользователя
    updateUserInfo();
    
    // Получаем ID опроса из URL
    const pollId = getPollIdFromUrl();
    if (!pollId) {
        showError('Опрос не найден');
        return;
    }

    try {
        // Загружаем данные опроса с сервера
        const pollData = await loadPollResults(pollId);
        
        // Рендерим результаты
        renderResults(pollData);
        
    } catch (error) {
        console.error('Error initializing page:', error);
        showError(error.message || 'Произошла ошибка при загрузке данных');
    }
}

// Запускаем инициализацию когда DOM загружен
document.addEventListener('DOMContentLoaded', initPage);
