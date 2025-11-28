// dashboard/dashboard.js
class Dashboard {
    constructor() {
        this.polls = [];
    }

    async init() {
        console.log('Dashboard initialized');
        
        // Проверка авторизации БЕЗ автоматического перенаправления
        if (!this.checkAuth()) return;

        // Настраиваем обработчики событий
        this.setupEventListeners();
        
        // Обновляем информацию пользователя
        this.updateUserInfo();
        
        // Загружаем опросы с сервера
        await this.loadPolls();
        
        // Синхронизируем данные
        await this.syncData();
    }

    checkAuth() {
        const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
        if (!isAuthenticated) {
            // Показываем сообщение и перенаправляем
            alert('Пожалуйста, авторизуйтесь');
            window.location.href = '../index/index.html';
            return false;
        }
        return true;
    }

    // ... остальные методы без изменений ...
    setupEventListeners() {
        // Logout functionality
        document.getElementById('logoutBtn').addEventListener('click', () => {
            this.handleLogout();
        });
    }

    updateUserInfo() {
        const userData = localStorage.getItem('userData');
        if (userData) {
            try {
                const user = JSON.parse(userData);
                document.getElementById('userName').textContent = 
                    user.name || `Студент ${user.id}`;
                document.getElementById('userFaculty').textContent = 
                    user.faculty || 'Факультет информатики';
                
                // Обновляем аватар
                const avatar = document.getElementById('userAvatar');
                if (avatar && user.name) {
                    avatar.textContent = user.name.charAt(0).toUpperCase();
                }
            } catch (error) {
                console.error('Error parsing user data:', error);
            }
        }
    }

    async loadPolls() {
        try {
            this.showLoading();
            
            // Загружаем опросы с сервера через DataService
            this.polls = await DataService.getPolls();
            console.log('Polls loaded from server:', this.polls);
            
            if (this.polls && this.polls.length > 0) {
                this.renderPolls();
            } else {
                this.showEmptyState();
            }
            
        } catch (error) {
            console.error('Error loading polls:', error);
            this.showError('Не удалось загрузить опросы');
        }
    }

    renderPolls() {
        const pollsGrid = document.getElementById('pollsGrid');
        
        pollsGrid.innerHTML = this.polls.map(poll => {
            const hasVoted = DataService.hasVoted(poll.id);
            const isExpired = this.isPollExpired(poll.endDate);
            
            return `
                <div class="poll-card" data-poll-id="${poll.id}">
                    <div class="poll-header">
                        <h3 class="poll-title">${poll.title}</h3>
                        <div class="poll-status ${isExpired ? 'expired' : 'active'}">
                            ${isExpired ? 'Завершен' : 'Активен'}
                        </div>
                    </div>
                    <p class="poll-description">${poll.description}</p>
                    <div class="poll-meta">
                        <div class="poll-stats">
                            <i class="fas fa-users"></i>
                            <span>${poll.totalVotes || 0} голосов</span>
                        </div>
                        <div class="poll-info">
                            <div class="poll-info-item">
                                <i class="fas fa-clock"></i>
                                <span>${this.formatDate(poll.endDate)}</span>
                            </div>
                            <div class="poll-info-item">
                                <i class="fas fa-user-secret"></i>
                                <span>Анонимно</span>
                            </div>
                        </div>
                    </div>
                    <div class="participate-section">
                        <button class="participate-btn ${isExpired ? 'disabled' : ''}" 
                                data-poll-id="${poll.id}"
                                ${isExpired ? 'disabled' : ''}>
                            <i class="fas fa-${hasVoted ? 'chart-bar' : 'vote-yea'}"></i>
                            ${isExpired ? 'Опрос завершен' : 
                              hasVoted ? 'Посмотреть результаты' : 'Участвовать в опросе'}
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        // Добавляем обработчики для новых кнопок
        this.bindPollEvents();
    }

    bindPollEvents() {
        document.addEventListener('click', (e) => {
            const participateBtn = e.target.closest('.participate-btn');
            if (participateBtn && !participateBtn.disabled) {
                e.preventDefault();
                const pollId = participateBtn.getAttribute('data-poll-id');
                this.handlePollClick(pollId, participateBtn);
            }
        });
    }

    handlePollClick(pollId, button) {
        if (!pollId) {
            console.error('Poll ID is missing');
            return;
        }

        const poll = this.polls.find(p => p.id == pollId);
        if (!poll) {
            console.error('Poll not found:', pollId);
            return;
        }

        const hasVoted = DataService.hasVoted(pollId);
        const isExpired = this.isPollExpired(poll.endDate);

        if (isExpired || hasVoted) {
            // Переходим на страницу результатов
            window.location.href = `../results/results.html?pollId=${pollId}`;
        } else {
            // Переходим на страницу голосования
            window.location.href = `../poll/poll.html?pollId=${pollId}`;
        }
    }

    isPollExpired(endDate) {
        if (!endDate) return false;
        return new Date() > new Date(endDate);
    }

    formatDate(dateString) {
        if (!dateString) return 'Дата не указана';
        try {
            const date = new Date(dateString);
            const now = new Date();
            
            if (date < now) {
                return 'Завершен';
            }
            
            const options = { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            };
            return `До ${date.toLocaleDateString('ru-RU', options)}`;
        } catch (error) {
            return 'Ошибка даты';
        }
    }

    showLoading() {
        const pollsGrid = document.getElementById('pollsGrid');
        pollsGrid.innerHTML = `
            <div class="loading-state">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Загрузка опросов...</p>
            </div>
        `;
    }

    showEmptyState() {
        const pollsGrid = document.getElementById('pollsGrid');
        pollsGrid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <h3>Нет доступных опросов</h3>
                <p>В данный момент нет активных опросов для голосования.</p>
            </div>
        `;
    }

    showError(message) {
        const pollsGrid = document.getElementById('pollsGrid');
        pollsGrid.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Ошибка загрузки</h3>
                <p>${message}</p>
                <button class="retry-btn" onclick="window.location.reload()">
                    <i class="fas fa-redo"></i>
                    Попробовать снова
                </button>
            </div>
        `;
    }

    async syncData() {
        try {
            const syncedCount = await DataService.syncPendingVotes();
            if (syncedCount > 0) {
                console.log(`Синхронизировано ${syncedCount} голосов`);
            }
        } catch (error) {
            console.error('Sync error:', error);
        }
    }

    handleLogout() {
        if (confirm('Вы уверены, что хотите выйти из системы?')) {
            // Очищаем localStorage
            localStorage.removeItem('isAuthenticated');
            localStorage.removeItem('userData');
            localStorage.removeItem('authToken');
            localStorage.removeItem('studentId');
            
            // Перенаправляем на страницу авторизации
            window.location.href = '../index/index.html';
        }
    }
}

// Инициализация dashboard
document.addEventListener('DOMContentLoaded', () => {
    new Dashboard().init();
});