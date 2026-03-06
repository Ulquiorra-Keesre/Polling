// frontend/src/services/AuthService.js
import { DataService } from './DataService';

const USE_FAKE_TOKENS = false;

const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER: 'user_data',
  AUTH: 'auth_status',
  TOKEN_EXPIRY: 'token_expiry'
};

export const USER_ROLES = {
  GUEST: 'guest',
  USER: 'user',
  ADMIN: 'admin'
};

const ROLE_HIERARCHY = {
  [USER_ROLES.GUEST]: 0,
  [USER_ROLES.USER]: 1,
  [USER_ROLES.ADMIN]: 2
};

export const AuthService = {

  async login(studentId) {
    try {
      const result = await DataService.login(studentId);
      
      if (result.success && result.access_token) {
        this._saveTokens(result.access_token, result.refresh_token, result.expires_in);
        this._saveUser(result.user);
        localStorage.setItem(STORAGE_KEYS.AUTH, 'true');
        
        return { 
          success: true, 
          user: result.user, 
          role: result.user.role,
          isLocal: false
        };
      } else {
        return { 
          success: false, 
          error: result.error || 'Ошибка авторизации' 
        };
      }
    } catch (error) {
      console.error('Login failed:', error);
      
      return { 
        success: false, 
        error: 'Сервер недоступен. Убедитесь, что backend запущен на http://localhost:8000' 
      };
    }
  },

  /**
   * Обновление access токена через refresh токен
   */
  async refreshAccessToken() {
    try {
      const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
      
      // Если нет токена или он фейковый — не можем обновить
      if (!refreshToken || refreshToken.startsWith('fake_token_')) {
        console.warn('Cannot refresh: no valid refresh token');
        return false;
      }
      
      const result = await DataService.refreshToken(refreshToken);
      
      if (result.success && result.access_token) {
        this._saveTokens(result.access_token, result.refresh_token, result.expires_in);
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  },

  /**
   * Проверка авторизации с авто-обновлением токена
   */
  async checkAuth() {
    const isAuth = localStorage.getItem(STORAGE_KEYS.AUTH) === 'true';
    const accessToken = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    
    // Если нет авторизации или токена — не авторизован
    if (!isAuth || !accessToken) {
      return false;
    }
    
    // Если токен фейковый — не считаем валидным для лабы
    if (accessToken.startsWith('fake_token_')) {
      console.warn('Fake token detected, requiring re-auth');
      this.logout();
      return false;
    }
    
    // Проверяем, не истёк ли токен
    const expiry = localStorage.getItem(STORAGE_KEYS.TOKEN_EXPIRY);
    if (expiry && Date.now() >= parseInt(expiry)) {
      console.log('Access token expired, attempting refresh...');
      
      const refreshed = await this.refreshAccessToken();
      
      if (!refreshed) {
        // Не удалось обновить — выходим
        this.logout();
        return false;
      }
    }
    
    return true;
  },

  /**
   * Выход из системы
   */
  async logout() {
    const accessToken = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    
    // Отправляем запрос на сервер только для реальных токенов
    if (accessToken && !accessToken.startsWith('fake_token_')) {
      try {
        await DataService.logout(accessToken);
      } catch (error) {
        console.warn('Logout API call failed, clearing local storage anyway');
      }
    }
    
    // Очищаем localStorage в любом случае
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key);
    });
    
    // Редирект на страницу входа
    window.location.href = '/login';
  },

  /**
   * Получение текущей роли пользователя
   */
  getUserRole() {
    const user = this.getCurrentUser();
    return user?.role || localStorage.getItem('user_role') || USER_ROLES.GUEST;
  },

  /**
   * Проверка наличия одной из разрешённых ролей
   */
  hasRole(allowedRoles) {
    const currentRole = this.getUserRole();
    const roles = Array.isArray(allowedRoles) ? allowedRoles : [allowedRoles];
    return roles.includes(currentRole);
  },

  /**
   * Проверка минимального уровня роли
   */
  hasMinimumRole(minRole) {
    const currentRole = this.getUserRole();
    const currentLevel = ROLE_HIERARCHY[currentRole] || 0;
    const minLevel = ROLE_HIERARCHY[minRole] || 0;
    return currentLevel >= minLevel;
  },

  /**
   * Получение данных текущего пользователя
   */
  getCurrentUser() {
    const userStr = localStorage.getItem(STORAGE_KEYS.USER);
    return userStr ? JSON.parse(userStr) : null;
  },

  /**
   * Получение student_id текущего пользователя
   */
  getStudentId() {
    const user = this.getCurrentUser();
    return user ? user.student_id : null;
  },

  /**
   * Получение access токена
   */
  getAccessToken() {
    return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  },

  /**
   * Проверка на роль администратора
   */
  isAdmin() {
    return this.hasRole(USER_ROLES.ADMIN);
  },

  /**
   * Проверка на роль пользователя (user или admin)
   */
  isUser() {
    return this.hasRole([USER_ROLES.USER, USER_ROLES.ADMIN]);
  },

  _saveTokens(accessToken, refreshToken, expiresIn) {
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, accessToken);
    localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
    
    // Сохраняем время истечения с запасом 30 секунд
    const expiryTime = Date.now() + (expiresIn * 1000) - 30000;
    localStorage.setItem(STORAGE_KEYS.TOKEN_EXPIRY, expiryTime.toString());
  },

  _saveUser(user) {
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
    localStorage.setItem('user_role', user.role);
  }
};