// dashboard/dashboard.js
import AuthService from '../js/auth.js';
import pollManager from '../js/pollManager.js';

class Dashboard {
    constructor() {
        this.pollManager = pollManager;
    }

    async init() {
        if (!AuthService.requireAuth()) return;

        this.bindEvents();
        await this.loadPolls();
        this.updateUserInfo();
    }

    async loadPolls() {
        try {
            this.showLoading();
            
            // Загружаем опросы - теперь только реальные данные
            await this.pollManager.loadPolls();
            this.renderPolls();
            
        } catch (error) {
            console.error('Failed to load polls:', error);
            this.showError('Не удалось загрузить опросы');
        } finally {
            this.hideLoading();
        }
    }

    renderPolls() {
        const pollsGrid = document.getElementById('pollsGrid');
        const polls = this.pollManager.getActivePolls();

        if (polls.length === 0) {
            pollsGrid.innerHTML = `
                <div class="no-polls">
                    <i class="fas fa-inbox"></i>
                    <h3>Нет доступных опросов</h3>
                    <p>В данный момент нет активных опросов для голосования.</p>
                </div>
            `;
            return;
        }

        pollsGrid.innerHTML = polls.map(poll => this.createPollCard(poll)).join('');
        this.bindPollCardEvents();
    }

    createPollCard(poll) {
        const status = this.pollManager.getPollStatus(poll);
        const timeRemaining = this.pollManager.getTimeRemaining(poll.endDate);
        const hasVoted = this.pollManager.hasUserVoted(poll.id);

        return `
            <div class="poll-card" data-poll-id="${poll.id}">
                <div class="poll-header">
                    <h3 class="poll-title">${poll.title}</h3>
                    <span class="poll-status ${status.class}">${status.text}</span>
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
                            <span>${timeRemaining}</span>
                        </div>
                        <div class="poll-info-item">
                            <i class="fas fa-user-secret"></i>
                            <span>Анонимно</span>
                        </div>
                    </div>
                </div>
                <div class="participate-section">
                    <button class="participate-btn" data-poll-id="${poll.id}">
                        <i class="fas fa-${hasVoted ? 'chart-bar' : 'vote-yea'}"></i>
                        ${hasVoted ? 'Посмотреть результаты' : 'Участвовать в опросе'}
                    </button>
                </div>
            </div>
        `;
    }

    bindPollCardEvents() {
        document.querySelectorAll('.participate-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const pollId = e.target.closest('.participate-btn').dataset.pollId;
                this.handlePollClick(pollId);
            });
        });
    }

    handlePollClick(pollId) {
        const hasVoted = this.pollManager.hasUserVoted(pollId);
        
        if (hasVoted) {
            window.location.href = `../results/results.html?pollId=${pollId}`;
        } else {
            window.location.href = `../poll/poll.html?pollId=${pollId}`;
        }
    }

    showLoading() {
        const pollsGrid = document.getElementById('pollsGrid');
        pollsGrid.innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Загрузка опросов...</p>
            </div>
        `;
    }

    hideLoading() {
        // Убираем индикатор загрузки - renderPolls уже обновил контент
    }

    showError(message) {
        const pollsGrid = document.getElementById('pollsGrid');
        pollsGrid.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Ошибка загрузки</h3>
                <p>${message}</p>
                <button class="retry-btn" onclick="location.reload()">
                    <i class="fas fa-redo"></i>
                    Попробовать снова
                </button>
            </div>
        `;
    }

    updateUserInfo() {
        const user = AuthService.getCurrentUser();
        if (user && document.querySelector('.user-details h2')) {
            document.querySelector('.user-details h2').textContent = 
                user.name || `Студент ${user.id}`;
        }
    }

    bindEvents() {
        // Логика выхода
        document.querySelector('.logout-btn').addEventListener('click', () => {
            if (confirm('Вы уверены, что хотите выйти?')) {
                AuthService.logout();
            }
        });
    }
}

// Инициализация dashboard
document.addEventListener('DOMContentLoaded', function() {
    new Dashboard().init();
});