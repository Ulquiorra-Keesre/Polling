// js/auth.js
const AuthService = {
    async login(studentId) {
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
    },

    localLogin(studentId) {
        if (studentId.trim()) {
            const userData = {
                id: studentId,
                name: `Студент ${studentId}`,
                faculty: 'Факультет информатики',
                isLocal: true
            };
            
            this.saveUserData(userData);
            return { success: true, user: userData, isLocal: true };
        }
        return { success: false, error: 'Введите номер студенческого' };
    },

    saveUserData(userData) {
        localStorage.setItem(Config.STORAGE_KEYS.USER, JSON.stringify(userData));
        localStorage.setItem(Config.STORAGE_KEYS.AUTH, 'true');
    },

    logout() {
        Object.values(Config.STORAGE_KEYS).forEach(key => {
            localStorage.removeItem(key);
        });
        window.location.href = '../index/index.html';
    },

    isAuthenticated() {
        return localStorage.getItem(Config.STORAGE_KEYS.AUTH) === 'true';
    },

    getCurrentUser() {
        const userStr = localStorage.getItem(Config.STORAGE_KEYS.USER);
        return userStr ? JSON.parse(userStr) : null;
    },

    requireAuth() {
        if (!this.isAuthenticated()) {
            alert('Пожалуйста, авторизуйтесь');
            window.location.href = '../index/index.html';
            return false;
        }
        return true;
    },

    getStudentId() {
        const user = this.getCurrentUser();
        return user ? user.id : null;
    }
};

// Сделать глобальной
window.AuthService = AuthService;