// src/services/DataService.js
const API_BASE_URL = 'http://localhost:8000/api';
const STORAGE_KEYS = {
  POLLS_CACHE: 'polls_cache',
  SYNC_QUEUE: 'sync_queue',
  AUTH_TOKEN: 'auth_token',
  USER: 'user_data'
};

export const DataService = {
  // Общий метод для HTTP запросов
  async request(endpoint, options = {}) {
    try {
      const url = `${API_BASE_URL}${endpoint}`;
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

  // === АВТОРИЗАЦИЯ ===
  async login(studentId) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ 
        student_id: studentId,
        name: `Студент ${studentId}`,
        faculty: 'Факультет информатики'
      })
    });
    
    if (response.access_token) {
      localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, response.access_token);
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(response.user));
      localStorage.setItem('auth_status', 'true');
    }
    
    return { success: true, user: response.user };
  },

  // === ОПРОСЫ ===
  async getPolls() {
    try {
      const polls = await this.request('/polls');
      this.cachePolls(polls);
      return polls;
    } catch (error) {
      console.warn('Backend недоступен, используем кэш:', error);
      return this.getCachedPolls();
    }
  },

  async getPollById(pollId) {
    try {
      return await this.request(`/polls/${pollId}`);
    } catch (error) {
      console.warn('Backend недоступен, ищем в кэше:', error);
      const cachedPolls = this.getCachedPolls();
      return cachedPolls.find(poll => poll.id == pollId) || null;
    }
  },

  async getPollResults(pollId) {
    try {
      return await this.request(`/polls/${pollId}/results`);
    } catch (error) {
      console.warn('Backend недоступен:', error);
      return null;
    }
  },

  // === ГОЛОСОВАНИЕ ===
  async vote(pollId, optionId) {
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
      
      this.saveVoteLocally(pollId, optionId);
      this.removeFromSyncQueue(pollId, studentId);
      
      return result;
    } catch (error) {
      console.warn('Backend недоступен, сохраняем локально:', error);
      this.saveVoteLocally(pollId, optionId);
      this.addToSyncQueue(voteData);
      return { success: true, synced: false };
    }
  },

  async checkVote(pollId) {
    try {
      return await this.request(`/votes/check/${pollId}`);
    } catch (error) {
      console.warn('Backend недоступен, проверяем локально:', error);
      return { 
        has_voted: this.hasVotedLocally(pollId), 
        poll_id: pollId 
      };
    }
  },

  // === ЛОКАЛЬНОЕ ХРАНЕНИЕ ===
  cachePolls(polls) {
    const cacheData = {
      polls: polls,
      timestamp: Date.now()
    };
    localStorage.setItem(STORAGE_KEYS.POLLS_CACHE, JSON.stringify(cacheData));
  },

  getCachedPolls() {
    const cached = localStorage.getItem(STORAGE_KEYS.POLLS_CACHE);
    if (!cached) return [];
    
    try {
      const cacheData = JSON.parse(cached);
      const isExpired = Date.now() - cacheData.timestamp > (5 * 60 * 1000); // 5 минут
      
      return isExpired ? [] : cacheData.polls;
    } catch (error) {
      console.error('Error parsing cached polls:', error);
      return [];
    }
  },

  saveVoteLocally(pollId, optionId) {
    const studentId = this.getCurrentUser()?.student_id;
    if (!studentId) return;
    
    const voteKey = `vote_${pollId}_${studentId}`;
    localStorage.setItem(voteKey, optionId);
    localStorage.setItem(`${voteKey}_time`, new Date().toISOString());
  },

  hasVotedLocally(pollId) {
    const studentId = this.getCurrentUser()?.student_id;
    if (!studentId) return false;
    
    const voteKey = `vote_${pollId}_${studentId}`;
    return localStorage.getItem(voteKey) !== null;
  },

  addToSyncQueue(voteData) {
    const queue = this.getSyncQueue();
    
    const filteredQueue = queue.filter(vote => 
      !(vote.poll_id == voteData.poll_id && vote.student_id === voteData.student_id)
    );
    
    filteredQueue.push({
      ...voteData,
      timestamp: new Date().toISOString()
    });
    
    localStorage.setItem(STORAGE_KEYS.SYNC_QUEUE, JSON.stringify(filteredQueue));
  },

  removeFromSyncQueue(pollId, studentId) {
    const queue = this.getSyncQueue();
    const newQueue = queue.filter(vote => 
      !(vote.poll_id == pollId && vote.student_id === studentId)
    );
    localStorage.setItem(STORAGE_KEYS.SYNC_QUEUE, JSON.stringify(newQueue));
  },

  getSyncQueue() {
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.SYNC_QUEUE) || '[]');
  },

  async syncPendingVotes() {
    const queue = this.getSyncQueue();
    const successfulSyncs = [];
    
    for (const vote of queue) {
      try {
        await this.request('/votes', {
          method: 'POST',
          body: JSON.stringify(vote)
        });
        successfulSyncs.push(vote);
      } catch (error) {
        console.warn('Не удалось синхронизировать голос:', vote, error);
      }
    }
    
    // Удаляем успешно синхронизированные голоса
    successfulSyncs.forEach(vote => {
      this.removeFromSyncQueue(vote.poll_id, vote.student_id);
    });
    
    return successfulSyncs.length;
  },

  // === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
  getAuthToken() {
    return localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
  },

  getCurrentUser() {
    const userStr = localStorage.getItem(STORAGE_KEYS.USER);
    return userStr ? JSON.parse(userStr) : null;
  },

  handleUnauthorized() {
    localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER);
    localStorage.removeItem('auth_status');
    window.location.href = '/login';
  }
};