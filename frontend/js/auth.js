// js/auth.js
import Config from './config.js';
import dataService from './dataService.js';

class AuthService {
    static async login(studentId) {
        try {
            // Пробуем авторизацию через бэкенд
            const response = await fetch(`${Config.API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ studentId })
            });

            if (response.ok) {
                const userData = await response.json();
                this.saveUserData(userData);
                return { success: true, user: userData };
            } else {
                throw new Error('Ошибка авторизации');
            }
        } catch (error) {
            console.log('Backend недоступен, используем локальную авторизацию');
            return this.localLogin(studentId);
        }
    }

    static localLogin(studentId) {
        if (studentId.trim()) {
            const userData = {
                id: studentId,
                name: `Студент ${studentId}`,
                faculty: 'Факультет информатики',
                isLocal: true // пометка для оффлайн режима
            };
            
            this.saveUserData(userData);
            return { success: true, user: userData, isLocal: true };
        }
        return { success: false, error: 'Введите номер студенческого' };
    }

    static saveUserData(userData) {
        localStorage.setItem(Config.STORAGE_KEYS.USER, JSON.stringify(userData));
        localStorage.setItem(Config.STORAGE_KEYS.AUTH, 'true');
    }

    static logout() {
        Object.values(Config.STORAGE_KEYS).forEach(key => {
            localStorage.removeItem(key);
        });
    }

    static isAuthenticated() {
        return localStorage.getItem(Config.STORAGE_KEYS.AUTH) === 'true';
    }

    static getCurrentUser() {
        const userStr = localStorage.getItem(Config.STORAGE_KEYS.USER);
        return userStr ? JSON.parse(userStr) : null;
    }

    static requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = '../index.html';
            return false;
        }
        return true;
    }
}

export default AuthService;