// src/services/AuthService.js
import { DataService } from './DataService';

const STORAGE_KEYS = {
  USER: 'user_data',
  AUTH: 'auth_status',
  AUTH_TOKEN: 'auth_token'
};

export const AuthService = {
  async login(studentId) {
    try {
      // Пробуем авторизацию через бэкенд
      const result = await DataService.login(studentId);
      
      if (result.success) {
        return result;
      } else {
        // Fallback на локальную авторизацию
        return this.localLogin(studentId);
      }
    } catch (error) {
      console.warn('Backend недоступен, используем локальную авторизацию');
      return this.localLogin(studentId);
    }
  },

  localLogin(studentId) {
    if (studentId.trim()) {
      const userData = {
        id: studentId,
        student_id: studentId,
        name: `Студент ${studentId}`,
        faculty: 'Факультет информатики',
        is_local: true
      };
      
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
      localStorage.setItem(STORAGE_KEYS.AUTH, 'true');
      
      return { 
        success: true, 
        user: userData, 
        isLocal: true 
      };
    }
    return { success: false, error: 'Введите номер студенческого' };
  },

  logout() {
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key);
    });
    window.location.href = '/login';
  },

  async checkAuth() {
    const isAuth = localStorage.getItem(STORAGE_KEYS.AUTH) === 'true';
    if (isAuth) {
      // Проверяем токен с сервером если есть
      const token = localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
      if (token) {
        try {
          // Можно добавить проверку токена с сервером
          return true;
        } catch (error) {
          this.logout();
          return false;
        }
      }
      return true;
    }
    return false;
  },

  getCurrentUser() {
    const userStr = localStorage.getItem(STORAGE_KEYS.USER);
    return userStr ? JSON.parse(userStr) : null;
  },

  getStudentId() {
    const user = this.getCurrentUser();
    return user ? user.student_id : null;
  }
};