// js/dataService.js
(function() {
    const DataService = {
        baseURL: Config.API_BASE_URL,

        // Общий метод для HTTP запросов
        request: async function(endpoint, options = {}) {
            try {
                const url = `${this.baseURL}${endpoint}`;
                const defaultOptions = {
                    headers: {
                        'Content-Type': 'application/json',
                    }
                };

                // Добавляем токен авторизации
                const token = this.getAuthToken();
                if (token) {
                    defaultOptions.headers['Authorization'] = `Bearer ${token}`;
                }

                const response = await fetch(url, { ...defaultOptions, ...options });
                
                if (!response.ok) {
                    // Если 401 - неавторизован, перенаправляем на логин
                    if (response.status === 401) {
                        this.handleUnauthorized();
                        throw new Error('Требуется авторизация');
                    }
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error('API request failed:', error);
                throw error;
            }
        },

        // Обработка неавторизованного доступа
        handleUnauthorized: function() {
            localStorage.removeItem(Config.STORAGE_KEYS.AUTH_TOKEN);
            localStorage.removeItem(Config.STORAGE_KEYS.USER);
            localStorage.removeItem(Config.STORAGE_KEYS.AUTH);
            // Можно добавить перенаправление на страницу логина
            window.location.href = '../index/index.html';
        },

        // === АВТОРИЗАЦИЯ ===
        login: async function(studentId) {
            try {
                const response = await this.request('/auth/login', {
                    method: 'POST',
                    body: JSON.stringify({ 
                        student_id: studentId,
                        name: `Студент ${studentId}`,
                        faculty: 'Факультет информатики'
                    })
                });
                
                // Сохраняем токен и данные пользователя
                if (response.access_token) {
                    localStorage.setItem(Config.STORAGE_KEYS.AUTH_TOKEN, response.access_token);
                    localStorage.setItem(Config.STORAGE_KEYS.USER, JSON.stringify(response.user));
                    localStorage.setItem(Config.STORAGE_KEYS.AUTH, 'true');
                }
                
                return response;
            } catch (error) {
                console.warn('Backend недоступен, используем локальную авторизацию:', error);
                return this.localLogin(studentId);
            }
        },

        // Локальная авторизация (fallback)
        localLogin: function(studentId) {
            if (studentId.trim()) {
                const userData = {
                    id: studentId,
                    student_id: studentId,
                    name: `Студент ${studentId}`,
                    faculty: 'Факультет информатики',
                    is_local: true
                };
                
                localStorage.setItem(Config.STORAGE_KEYS.USER, JSON.stringify(userData));
                localStorage.setItem(Config.STORAGE_KEYS.AUTH, 'true');
                
                return { 
                    success: true, 
                    user: userData, 
                    isLocal: true 
                };
            }
            return { success: false, error: 'Введите номер студенческого' };
        },

        // === ОПРОСЫ ===
        getPolls: async function() {
            try {
                const polls = await this.request('/polls');
                this.cachePolls(polls);
                return polls;
            } catch (error) {
                console.warn('Backend недоступен, используем кэш:', error);
                return this.getCachedPolls();
            }
        },

        getPollById: async function(pollId) {
            try {
                return await this.request(`/polls/${pollId}`);
            } catch (error) {
                console.warn('Backend недоступен, ищем в кэше:', error);
                const cachedPolls = this.getCachedPolls();
                return cachedPolls.find(poll => poll.id == pollId) || null;
            }
        },

        getPollResults: async function(pollId) {
            try {
                return await this.request(`/polls/${pollId}/results`);
            } catch (error) {
                console.warn('Backend недоступен:', error);
                return null;
            }
        },

        // === ГОЛОСОВАНИЕ ===
        vote: async function(pollId, optionId) {
            const studentId = this.getCurrentUser()?.student_id;
            if (!studentId) {
                throw new Error('Пользователь не авторизован');
            }

            const voteData = {
                poll_id: parseInt(pollId),
                option_id: parseInt(optionId),
                student_id: studentId
            };

            try {
                const result = await this.request('/votes', {
                    method: 'POST',
                    body: JSON.stringify(voteData)
                });
                
                // Успешно отправили на сервер - сохраняем локально и удаляем из очереди
                this.saveVoteLocally(pollId, optionId);
                this.removeFromSyncQueue(pollId, studentId);
                
                return result;
            } catch (error) {
                console.warn('Backend недоступен, сохраняем локально:', error);
                // Сохраняем локально и добавляем в очередь синхронизации
                this.saveVoteLocally(pollId, optionId);
                this.addToSyncQueue(voteData);
                return { success: true, synced: false };
            }
        },

        checkVote: async function(pollId) {
            try {
                return await this.request(`/votes/check/${pollId}`);
            } catch (error) {
                console.warn('Backend недоступен, проверяем локально:', error);
                // Fallback на локальную проверку
                return { 
                    has_voted: this.hasVotedLocally(pollId), 
                    poll_id: pollId 
                };
            }
        },

        // === ЛОКАЛЬНОЕ ХРАНЕНИЕ ===
        cachePolls: function(polls) {
            const cacheData = {
                polls: polls,
                timestamp: Date.now()
            };
            localStorage.setItem(Config.STORAGE_KEYS.POLLS_CACHE, JSON.stringify(cacheData));
        },

        getCachedPolls: function() {
            const cached = localStorage.getItem(Config.STORAGE_KEYS.POLLS_CACHE);
            if (!cached) return [];
            
            try {
                const cacheData = JSON.parse(cached);
                const isExpired = Date.now() - cacheData.timestamp > Config.CACHE_DURATION;
                
                return isExpired ? [] : cacheData.polls;
            } catch (error) {
                console.error('Error parsing cached polls:', error);
                return [];
            }
        },

        saveVoteLocally: function(pollId, optionId) {
            const studentId = this.getCurrentUser()?.student_id;
            if (!studentId) return;
            
            const voteKey = `vote_${pollId}_${studentId}`;
            localStorage.setItem(voteKey, optionId);
            localStorage.setItem(`${voteKey}_time`, new Date().toISOString());
        },

        hasVotedLocally: function(pollId) {
            const studentId = this.getCurrentUser()?.student_id;
            if (!studentId) return false;
            
            const voteKey = `vote_${pollId}_${studentId}`;
            return localStorage.getItem(voteKey) !== null;
        },

        addToSyncQueue: function(voteData) {
            const queue = this.getSyncQueue();
            
            // Удаляем старую запись если есть
            const filteredQueue = queue.filter(vote => 
                !(vote.poll_id == voteData.poll_id && vote.student_id === voteData.student_id)
            );
            
            filteredQueue.push({
                ...voteData,
                timestamp: new Date().toISOString()
            });
            
            localStorage.setItem(Config.STORAGE_KEYS.SYNC_QUEUE, JSON.stringify(filteredQueue));
        },

        removeFromSyncQueue: function(pollId, studentId) {
            const queue = this.getSyncQueue();
            const newQueue = queue.filter(vote => 
                !(vote.poll_id == pollId && vote.student_id === studentId)
            );
            localStorage.setItem(Config.STORAGE_KEYS.SYNC_QUEUE, JSON.stringify(newQueue));
        },

        getSyncQueue: function() {
            return JSON.parse(localStorage.getItem(Config.STORAGE_KEYS.SYNC_QUEUE) || '[]');
        },

        // Синхронизация ожидающих голосов
        syncPendingVotes: async function() {
            const queue = this.getSyncQueue();
            const successfulSyncs = [];
            
            for (const vote of queue) {
                try {
                    await this.request('/votes', {
                        method: 'POST',
                        body: JSON.stringify(vote)
                    });
                    successfulSyncs.push(vote);
                    console.log('Успешно синхронизирован голос:', vote);
                } catch (error) {
                    console.warn('Не удалось синхронизировать голос:', vote, error);
                }
            }
            
            // Удаляем успешно синхронизированные голоса
            this.removeFromSyncQueue(successfulSyncs);
            return successfulSyncs.length;
        },

        // === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
        getAuthToken: function() {
            return localStorage.getItem(Config.STORAGE_KEYS.AUTH_TOKEN);
        },

        getCurrentUser: function() {
            const userStr = localStorage.getItem(Config.STORAGE_KEYS.USER);
            return userStr ? JSON.parse(userStr) : null;
        },

        isAuthenticated: function() {
            return localStorage.getItem(Config.STORAGE_KEYS.AUTH) === 'true';
        },

        logout: function() {
            Object.values(Config.STORAGE_KEYS).forEach(key => {
                localStorage.removeItem(key);
            });
        }
    };

    window.DataService = DataService;
})();