// frontend/src/services/DataService.js
import { AuthService } from './AuthService';

const API_BASE_URL = 'http://localhost:8000'; 
const STORAGE_KEYS = {
  POLLS_CACHE: 'polls_cache',
  SYNC_QUEUE: 'sync_queue',
  AUTH_TOKEN: 'auth_token',
  USER: 'user_data'
};

export const DataService = {
  async request(endpoint, options = {}) {
    const maxRetries = 1;
    let retryCount = 0;
    
    while (retryCount <= maxRetries) {
      try {
        const url = `${API_BASE_URL}${endpoint}`;
        console.log(`API Request: ${url}`); 
        
        const defaultOptions = {
          headers: {
            'Content-Type': 'application/json',
          }
        };

        // 🔹 Access token через AuthService
        const token = AuthService.getAccessToken();  // ← Теперь работает!
        if (token) {
          defaultOptions.headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(url, { ...defaultOptions, ...options });
        console.log(`Response status: ${response.status}`);
        
        // 🔹 Обработка 401 — пытаемся обновить токен
        if (response.status === 401) {
          const errorData = await response.json().catch(() => ({}));
          
          if (errorData.detail?.includes('истёк') || errorData.detail?.includes('expired')) {
            console.log('Token expired, attempting refresh...');
            
            const refreshed = await AuthService.refreshAccessToken();  // ← Теперь работает!
            
            if (refreshed) {
              console.log('Token refreshed, retrying request...');
              retryCount++;
              continue;
            }
          }
          
          AuthService.logout();
          throw new Error('Сессия истекла. Пожалуйста, войдите снова.');
        }
        
        // 🔹 Обработка 403
        if (response.status === 403) {
          throw new Error('Недостаточно прав для выполнения этого действия');
        }
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`Error response: ${errorText}`);
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
        
      } catch (error) {
        if (retryCount < maxRetries && error.message?.includes('истёк')) {
          retryCount++;
          continue;
        }
        
        console.error('API request failed:', error);
        throw error;
      }
    }
    
    throw new Error('Превышено количество попыток обновления токена');
  },

//Обновление refresh токена
async refreshToken(refreshToken) {
  try {
    const response = await this.request('/api/auth/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken })
    });

    if (response.access_token) {
      return { 
        success: true,
        access_token: response.access_token,
        refresh_token: response.refresh_token,
        expires_in: response.expires_in
      };
    }
    
    return { 
      success: false, 
      error: response.detail || 'Failed to refresh token' 
    };
    
  } catch (error) {
    console.error('Refresh token error:', error);
    return { 
      success: false, 
      error: error.message || 'Ошибка обновления токена' 
    };
  }
},

//Выход из системы (отзыв токенов - ротация)
async logout(accessToken) {
  try {
    await fetch(`${API_BASE_URL}/api/auth/logout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      }
    });
  } catch (error) {
    console.warn('Logout API call failed:', error);
  }
},

  //AВТОРИЗАЦИЯ
async login(studentId) {
  try {
    console.log('=== LOGIN ATTEMPT ===');
    console.log('Student ID:', studentId);
    
    const response = await this.request('/api/auth/login', { 
      method: 'POST',
      body: JSON.stringify({ 
        student_id: studentId,
        name: `Студент ${studentId}`,
        faculty: 'Факультет информатики'
      })
    });

    console.log('Login response:', response);
    
    // 🔹 Backend возвращает токены напрямую, оборачиваем в ожидаемый формат:
    if (response.access_token) {
      return { 
        success: true,
        access_token: response.access_token,
        refresh_token: response.refresh_token,
        expires_in: response.expires_in,
        user: response.user
      };
    }
    
    // Если бэкенд вернул ошибку в другом формате
    return { 
      success: false, 
      error: response.detail || response.error || 'Неизвестная ошибка' 
    };
    
  } catch (error) {
    console.error('DataService.login error:', error);
    
    if (error.message && error.message.includes('422')) {
      return { 
        success: false, 
        error: 'Неверный формат данных для авторизации' 
      };
    }
    
    return { 
      success: false, 
      error: error.message || 'Ошибка авторизации' 
    };
  }
},

  // === ОПРОСЫ ===
  async getPolls() {
    try {
      const polls = await this.request('/api/polls'); 
      this.cachePolls(polls);
      return polls;
    } catch (error) {
      console.warn('Backend недоступен, используем кэш:', error);
      return this.getCachedPolls();
    }
  },

  async getPollById(pollId) {
    try {
      return await this.request(`/api/polls/${pollId}`); 
    } catch (error) {
      console.warn('Backend недоступен, ищем в кэше:', error);
      const cachedPolls = this.getCachedPolls();
      return cachedPolls.find(poll => poll.id == pollId) || null;
    }
  },

  async getPollResults(pollId) {
    try {
      return await this.request(`/api/polls/${pollId}/results`); 
    } catch (error) {
      console.warn('Backend недоступен:', error);
      return null;
    }
  },

  // === СОЗДАНИЕ ОПРОСА ===
  async createPoll(pollData) {
    try {
      return await this.request('/api/polls', { 
        method: 'POST',
        body: JSON.stringify(pollData)
      });
    } catch (error) {
      console.error('Create poll error:', error);
      throw error;
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
      const result = await this.request('/api/votes', { 
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
      return await this.request(`/api/votes/check/${pollId}`); 
    } catch (error) {
      console.warn('Backend недоступен, проверяем локально:', error);
      return { 
        has_voted: this.hasVotedLocally(pollId), 
        poll_id: pollId 
      };
    }
  },

  // === ЛОКАЛЬНОЕ ХРАНЕНИЕ 
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
      const isExpired = Date.now() - cacheData.timestamp > (5 * 60 * 1000); 
      
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
        await this.request('/api/votes', { 
          method: 'POST',
          body: JSON.stringify(vote)
        });
        successfulSyncs.push(vote);
      } catch (error) {
        console.warn('Не удалось синхронизировать голос:', vote, error);
      }
    }
    
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