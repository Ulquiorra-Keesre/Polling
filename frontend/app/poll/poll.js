// poll/poll.js
import AuthService from '../js/auth.js';
import pollManager from '../js/pollManager.js';

class PollPage {
    constructor() {
        this.selectedOption = null;
        this.currentPollId = null;
        this.currentPoll = null;
    }

    async init() {
        // Проверяем авторизацию
        if (!AuthService.requireAuth()) return;

        this.currentPollId = this.getPollIdFromURL();
        
        if (!this.currentPollId) {
            this.showError('Опрос не найден');
            return;
        }

        this.bindEvents();
        await this.loadPollData();
        this.updateUserInfo();
    }

    bindEvents() {
        // Кнопка выхода
        document.getElementById('logoutBtn').addEventListener('click', () => {
            this.handleLogout();
        });

        // Кнопка "Назад"
        document.getElementById('backBtn').addEventListener('click', (e) => {
            e.preventDefault();
            this.handleBackToPolls();
        });

        // Кнопка голосования
        document.getElementById('voteBtn').addEventListener('click', () => {
            this.handleVote();
        });
    }

    async loadPollData() {
        try {
            this.showLoading();
            
            // Загружаем данные опроса
            this.currentPoll = await pollManager.loadPoll(this.currentPollId);
            
            if (this.currentPoll) {
                this.renderPoll(this.currentPoll);
                
                // Проверяем, не голосовал ли уже пользователь
                if (pollManager.hasUserVoted(this.currentPollId)) {
                    this.showAlreadyVoted();
                }
            } else {
                this.showError('Опрос не найден');
            }
            
        } catch (error) {
            console.error('Error loading poll:', error);
            this.showError('Ошибка при загрузке опроса');
        }
    }

    renderPoll(poll) {
        // Обновляем информацию об опросе
        document.getElementById('pollTitle').textContent = poll.title;
        document.getElementById('pollDescription').textContent = poll.description;
        document.getElementById('pollEndDate').textContent = `Завершается: ${pollManager.formatDate(poll.endDate)}`;
        document.getElementById('pollTotalVotes').textContent = `${poll.totalVotes || 0} голосов`;

        // Рендерим варианты ответа
        this.renderOptions(poll.options);
    }

    renderOptions(options) {
        const optionCards = document.getElementById('optionCards');
        
        optionCards.innerHTML = options.map((option, index) => `
            <label class="option-card">
                <input type="radio" name="vote" value="${option.id}" class="option-input">
                <div class="option-content">
                    <div class="option-number">${index + 1}</div>
                    <div class="option-text">${option.text}</div>
                </div>
            </label>
        `).join('');

        // Добавляем обработчики для карточек
        this.bindOptionCards();
    }

    bindOptionCards() {
        const optionCards = document.querySelectorAll('.option-card');
        const voteBtn = document.getElementById('voteBtn');

        optionCards.forEach((card) => {
            card.addEventListener('click', () => {
                // Убираем выделение со всех карточек
                optionCards.forEach(c => c.classList.remove('selected'));
                
                // Добавляем выделение текущей карточке
                card.classList.add('selected');
                
                // Получаем выбранное значение
                const input = card.querySelector('.option-input');
                this.selectedOption = input.value;
                
                // Активируем кнопку голосования
                voteBtn.disabled = false;
                voteBtn.classList.add('active');
            });
        });
    }

    async handleVote() {
        if (!this.selectedOption) {
            alert('Пожалуйста, выберите вариант ответа');
            return;
        }

        try {
            const voteBtn = document.getElementById('voteBtn');
            voteBtn.disabled = true;
            voteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Отправка...';

            // Отправляем голос
            const result = await pollManager.vote(this.currentPollId, this.selectedOption);
            
            if (result.success) {
                // Перенаправляем на страницу результатов
                window.location.href = `../results/results.html?pollId=${this.currentPollId}`;
            } else {
                throw new Error('Ошибка при голосовании');
            }
            
        } catch (error) {
            console.error('Error voting:', error);
            alert('Ошибка при отправке голоса. Попробуйте еще раз.');
            
            // Восстанавливаем кнопку
            const voteBtn = document.getElementById('voteBtn');
            voteBtn.disabled = false;
            voteBtn.innerHTML = '<i class="fas fa-vote-yea"></i> Проголосовать';
        }
    }

    getPollIdFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('pollId') || urlParams.get('id');
    }

    updateUserInfo() {
        const user = AuthService.getCurrentUser();
        if (user) {
            document.getElementById('userName').textContent = user.name || `Студент ${user.id}`;
            document.getElementById('userFaculty').textContent = user.faculty || 'Факультет информатики';
            
            // Обновляем аватар
            const avatar = document.querySelector('.avatar');
            if (avatar && user.name) {
                avatar.textContent = user.name.charAt(0).toUpperCase();
            }
        }
    }

    showLoading() {
        const optionCards = document.getElementById('optionCards');
        optionCards.innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Загрузка вариантов ответа...</p>
            </div>
        `;
    }

    showAlreadyVoted() {
        // Если пользователь уже голосовал, перенаправляем на результаты
        window.location.href = `../results/results.html?pollId=${this.currentPollId}`;
    }

    showError(message) {
        const optionCards = document.getElementById('optionCards');
        optionCards.innerHTML = `
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

    handleLogout() {
        if (confirm('Вы уверены, что хотите выйти из системы?')) {
            AuthService.logout();
        }
    }

    handleBackToPolls() {
        if (this.selectedOption && !confirm('Вы уверены, что хотите вернуться? Ваш голос не будет сохранен.')) {
            return;
        }
        window.location.href = '../dashboard/dashboard.html';
    }
}

// Инициализация страницы
document.addEventListener('DOMContentLoaded', function() {
    new PollPage().init();
});