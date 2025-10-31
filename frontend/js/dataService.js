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
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error('API request failed:', error);
                throw error;
            }
        },

        // === АВТОРИЗАЦИЯ ===
        login: async function(studentId) {
            return await this.request(Config.ENDPOINTS.AUTH.LOGIN, {
                method: 'POST',
                body: JSON.stringify({ studentId })
            });
        },

        // === ОПРОСЫ ===
        getPolls: async function() {
            try {
                const polls = await this.request(Config.ENDPOINTS.POLLS.LIST);
                this.cachePolls(polls);
                return polls;
            } catch (error) {
                console.log('Using cached polls data');
                return this.getCachedPolls();
            }
        },

        getPollById: async function(pollId) {
            return await this.request(`${Config.ENDPOINTS.POLLS.GET}/${pollId}`);
        },

        getPollResults: async function(pollId) {
            return await this.request(`${Config.ENDPOINTS.POLLS.RESULTS}/${pollId}/results`);
        },

        // === ГОЛОСОВАНИЕ ===
        vote: async function(pollId, optionId) {
            const studentId = AuthService.getCurrentUser()?.id;
            const voteData = {
                pollId,
                optionId,
                studentId,
                timestamp: new Date().toISOString()
            };

            try {
                const result = await this.request(Config.ENDPOINTS.VOTES.CREATE, {
                    method: 'POST',
                    body: JSON.stringify(voteData)
                });
                
                this.saveVoteLocally(pollId, optionId);
                return result;
            } catch (error) {
                console.log('Saving vote locally');
                this.saveVoteLocally(pollId, optionId);
                this.addToSyncQueue(voteData);
                return { success: true, synced: false };
            }
        },

        checkVote: async function(pollId) {
            const studentId = AuthService.getCurrentUser()?.id;
            return await this.request(Config.ENDPOINTS.VOTES.CHECK, {
                method: 'POST',
                body: JSON.stringify({ pollId, studentId })
            });
        },

        // === ЛОКАЛЬНОЕ ХРАНЕНИЕ ===
        cachePolls: function(polls) {
            const cacheData = {
                polls,
                timestamp: Date.now()
            };
            localStorage.setItem(Config.STORAGE_KEYS.POLLS_CACHE, JSON.stringify(cacheData));
        },

        getCachedPolls: function() {
            const cached = localStorage.getItem(Config.STORAGE_KEYS.POLLS_CACHE);
            if (!cached) return [];
            
            const cacheData = JSON.parse(cached);
            const isExpired = Date.now() - cacheData.timestamp > Config.CACHE_DURATION;
            
            return isExpired ? [] : cacheData.polls;
        },

        saveVoteLocally: function(pollId, optionId) {
            const studentId = AuthService.getCurrentUser()?.id;
            const voteKey = `vote_${pollId}_${studentId}`;
            localStorage.setItem(voteKey, optionId);
        },

        hasVotedLocally: function(pollId) {
            const studentId = AuthService.getCurrentUser()?.id;
            const voteKey = `vote_${pollId}_${studentId}`;
            return localStorage.getItem(voteKey) !== null;
        },

        addToSyncQueue: function(voteData) {
            const queue = this.getSyncQueue();
            queue.push(voteData);
            localStorage.setItem(Config.STORAGE_KEYS.SYNC_QUEUE, JSON.stringify(queue));
        },

        getSyncQueue: function() {
            return JSON.parse(localStorage.getItem(Config.STORAGE_KEYS.SYNC_QUEUE) || '[]');
        },

        getAuthToken: function() {
            return localStorage.getItem(Config.STORAGE_KEYS.AUTH_TOKEN);
        }
    };

    window.DataService = DataService;
})();