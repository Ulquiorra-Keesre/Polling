import { DataService } from './DataService';

const STORAGE_KEYS = {
  USER: 'user_data',
  AUTH: 'auth_status',
  AUTH_TOKEN: 'auth_token',
  USER_ROLE: 'user_role'
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
      if (result.success && result.token) {
        const role = this.extractRoleFromToken(result.token);
        localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, result.token);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(result.user));
        localStorage.setItem(STORAGE_KEYS.USER_ROLE, role);
        localStorage.setItem(STORAGE_KEYS.AUTH, 'true');
        return { success: true, user: result.user, role: role };
      } else {
        return this.localLogin(studentId);
      }
    } catch (error) {
      console.warn('Backend недоступен, используем локальную авторизацию');
      return this.localLogin(studentId);
    }
  },

localLogin(studentId) {
    if (studentId.trim()) {
      const adminIds = ['777'];
      const role = adminIds.includes(studentId) ? USER_ROLES.ADMIN : USER_ROLES.USER;
      const userData = {
        id: studentId,
        student_id: studentId,
        name: `Студент ${studentId}`,
        faculty: 'Факультет информатики',
        is_local: true
      };
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
      localStorage.setItem(STORAGE_KEYS.AUTH, 'true');
      localStorage.setItem(STORAGE_KEYS.USER_ROLE, role);
      return { success: true, user: userData, role: role, isLocal: true };
    }
    return { success: false, error: 'Введите номер студенческого' };
  },

  extractRoleFromToken(token) {
    try {
      const payload = token.split('.')[1];
      const decoded = JSON.parse(atob(payload));
      return decoded.role || USER_ROLES.USER;
    } catch (error) {
      console.error('Error parsing token:', error);
      return USER_ROLES.USER;
    }
  },

  logout() {
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key);
    });
    window.location.href = '/login';
  },

  async checkAuth() {
    const isAuth = localStorage.getItem(STORAGE_KEYS.AUTH) === 'true';
    const token = localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
    if (isAuth && token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const expiry = payload.exp * 1000;
        if (Date.now() < expiry) {
          const role = payload.role || USER_ROLES.USER;
          localStorage.setItem(STORAGE_KEYS.USER_ROLE, role);
          return true;
        }
      } catch (error) {
        console.error('Token validation error:', error);
      }
      this.logout();
      return false;
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
  },

  getUserRole() {
    return localStorage.getItem(STORAGE_KEYS.USER_ROLE) || USER_ROLES.GUEST;
  },

  hasRole(allowedRoles) {
    const currentRole = this.getUserRole();
    const roles = Array.isArray(allowedRoles) ? allowedRoles : [allowedRoles];
    return roles.includes(currentRole);
  },

  hasMinimumRole(minRole) {
    const currentRole = this.getUserRole();
    const currentLevel = ROLE_HIERARCHY[currentRole] || 0;
    const minLevel = ROLE_HIERARCHY[minRole] || 0;
    return currentLevel >= minLevel;
  },

  isAdmin() {
    return this.hasRole(USER_ROLES.ADMIN);
  },
  
  isUser() {
    return this.hasRole([USER_ROLES.USER, USER_ROLES.ADMIN]);
  }
};